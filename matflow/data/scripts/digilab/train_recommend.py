import os
from io import BytesIO, StringIO

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

from uncertainty_engine import Client
from uncertainty_engine.graph import Graph
from uncertainty_engine.nodes.machine_learning import ModelConfig
from uncertainty_engine.nodes.resource_management import LoadDataset
from uncertainty_engine.nodes.machine_learning import TrainModel
from uncertainty_engine.nodes.resource_management import Save
from uncertainty_engine.nodes.workflow import Workflow
from uncertainty_engine.nodes.resource_management import LoadModel
from uncertainty_engine.nodes.machine_learning import PredictModel
from uncertainty_engine.nodes.resource_management import Download
from uncertainty_engine.nodes.base import Node


def upload_dataset(client, name, file_path, project_id):
    """Upload a datasets to the specified project."""
    return client.resources.upload(
        project_id=project_id,
        name=name,
        file_path=file_path,
        resource_type="dataset",
    )


def download_dataset(client, resource_name, project_id):
    dataset = client.resources.download(
        resource_id=client.resources.get_resource_id_by_name(
            name=resource_name,
            resource_type="dataset",
            project_id=project_id,
        ),
        project_id=project_id,
        resource_type="dataset",
    )

    return pd.read_csv(BytesIO(dataset))


def get_presigned_url(url):
    """
    Get the contents from the presigned url.
    """
    url = url.replace("https://", "http://")
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response


def plot_model_uncertainty(
    training_dpa, training_fs, visualise_means, visualise_stds, visualise_inputs
):
    """

    Plot the posterior mean and shaded plots of 67% and 99% confidence intervals.
    Overlay ground truth (optional) and samples at our

    """

    # Ensure that the data is the right shape

    training_dpa = training_dpa.to_numpy().flatten()
    training_fs = training_fs.to_numpy().flatten()
    visualise_means = visualise_means.to_numpy().flatten()
    visualise_stds = visualise_stds.to_numpy().flatten()
    visualise_inputs = visualise_inputs.to_numpy().flatten()

    # Confidence multipliers
    z67 = 1.0
    z99 = 2.576

    lower67 = visualise_means - z67 * visualise_stds
    upper67 = visualise_means + z67 * visualise_stds

    lower99 = visualise_means - z99 * visualise_stds
    upper99 = visualise_means + z99 * visualise_stds

    plt.figure(figsize=(7, 5))

    plt.fill_between(visualise_inputs, lower99, upper99, label="99% confidence")
    plt.fill_between(visualise_inputs, lower67, upper67, label="67% confidence")

    plt.plot(visualise_inputs, visualise_means, label="Predicted Mean")

    plt.scatter(training_dpa, training_fs, label="Samples", marker="x")
    plt.legend()
    plt.grid()
    plt.xlabel("Neutron Irradiation Dose (dpa)")
    plt.ylabel("Flexural Strength (MPa)")
    plt.xlim([-0.5, 5.5])
    plt.ylim([600, 1150])

    fig_name = "uncertainty_plot"
    plt.savefig(fig_name + ".png")


def train_model(client, project_ID, x_train_ID, y_train_ID, iter_idx):

    # Create a new graph
    train_graph = Graph()

    # Define the model config node
    model_config = ModelConfig(label="Model Config", client=client)

    # Add node to the graph and connect it to the train node
    train_graph.add_node(model_config)

    # Create datasets for x and y training data:
    x = LoadDataset(
        label="LoadDatasetX",
        project_id=project_ID,
        file_id=x_train_ID,
        client=client,
    )
    y = LoadDataset(
        label="LoadDatasetY",
        project_id=project_ID,
        file_id=y_train_ID,
        client=client,
    )

    train_graph.add_node(x)
    train_graph.add_node(y)

    # Create handles for the configuration and loaded dataset files
    output_config = model_config.make_handle("config")
    x_handle = x.make_handle("file")
    y_handle = y.make_handle("file")

    # Create the TrainModel node
    train_model = TrainModel(
        label="Train Model",
        config=output_config,
        inputs=x_handle,
        outputs=y_handle,
        client=client,
    )

    # Add the node to the graph
    train_graph.add_node(train_model)

    save_model = Save(
        label="SaveModel",
        data=train_model.make_handle("model"),
        project_id=project_ID,
        file_name=f"my-machine-learning-model_{iter_idx}",
        client=client,
    )

    train_graph.add_node(save_model)

    # Wrap the graph in a workflow node
    train_workflow = Workflow(
        graph=train_graph.nodes,
        inputs=train_graph.external_input,
        external_input_id=train_graph.external_input_id,
        client=client,
    )
    train_response = client.run_node(train_workflow)
    assert train_response.status.value == "completed"

    model_res_ID = client.resources.get_resource_id_by_name(
        name=f"my-machine-learning-model_{iter_idx}",
        resource_type="model",
        project_id=project_ID,
    )
    return model_res_ID


def predict(client, project_ID, model_ID, iter_idx):

    predict_graph = Graph()

    create_slice = Node(
        node_name="CreateDatasetSlice",
        label="Create dataset slice",
        variable="x",
        min=0,
        max=6,
        client=client,
    )
    predict_graph.add_node(create_slice)

    load_model = LoadModel(
        label="LoadModel",
        project_id=project_ID,
        file_id=model_ID,
        client=client,
    )
    predict_graph.add_node(load_model)

    predict = PredictModel(
        label="Predict",
        dataset=create_slice.make_handle("data"),
        model=load_model.make_handle("file"),
        client=client,
    )
    predict_graph.add_node(predict)

    save_x = Save(
        label="Save x data",
        data=create_slice.make_handle("data"),
        file_name=f"visualise_inputs_{iter_idx}",
        project_id=project_ID,
        client=client,
    )
    predict_graph.add_node(save_x)

    save_mean = Save(
        label="Save prediction mean",
        data=predict.make_handle("prediction"),
        file_name=f"mean_{iter_idx}",
        project_id=project_ID,
        client=client,
    )
    predict_graph.add_node(save_mean)

    save_std = Save(
        label="Save prediction std dev",
        data=predict.make_handle("uncertainty"),
        file_name=f"std_{iter_idx}",
        project_id=project_ID,
        client=client,
    )
    predict_graph.add_node(save_std)

    # Add handles to the prediction and uncertainty outputs
    output_predictions = predict.make_handle("prediction")
    output_uncertainty = predict.make_handle("uncertainty")

    plot = Node(
        node_name="UncertaintyPlot",
        label="plot",
        client=client,
        X=create_slice.make_handle("data"),
        prediction=output_predictions,
        uncertainty=output_uncertainty,
    )
    predict_graph.add_node(plot)

    # Define download nodes for predictions and uncertainty
    download_predictions = Download(
        label="Download Predictions",
        file=output_predictions,
        client=client,
    )
    download_uncertainty = Download(
        label="Download Uncertainty",
        file=output_uncertainty,
        client=client,
    )

    # Add download nodes to the graph and connect them to the predict node
    predict_graph.add_node(download_predictions)
    predict_graph.add_node(download_uncertainty)

    # Define the output handles for the download nodes
    output_download_predictions = download_predictions.make_handle("file")
    output_download_uncertainty = download_uncertainty.make_handle("file")

    # Wrap the graph in a workflow node
    predict_workflow = Workflow(
        graph=predict_graph.nodes,
        inputs=predict_graph.external_input,
        external_input_id=predict_graph.external_input_id,
        requested_output={
            "Predictions": output_download_predictions.model_dump(),
            "Uncertainty": output_download_uncertainty.model_dump(),
        },
        client=client,
    )
    predict_response = client.run_node(predict_workflow)
    assert predict_response.status.value == "completed"

    # Download the predictions and save as a DataFrame
    predictions_response = get_presigned_url(
        predict_response.outputs["outputs"]["Predictions"]
    )
    predictions_df = pd.read_csv(StringIO(predictions_response.text))

    # Download the uncertainty and save as a DataFrame
    uncertainty_response = get_presigned_url(
        predict_response.outputs["outputs"]["Uncertainty"]
    )
    uncertainty_df = pd.read_csv(StringIO(uncertainty_response.text))

    y_pred = predictions_df.to_numpy().flatten()
    y_std = uncertainty_df.to_numpy().flatten()

    return y_pred, y_std


def recommend_next_x(client, project_ID, model_ID):

    recommend_graph = Graph()

    load_model = LoadModel(
        label="LoadModel",
        project_id=project_ID,
        file_id=model_ID,
        client=client,
    )
    recommend_graph.add_node(load_model)

    recommend = Node(
        node_name="Recommend",
        label="Recommend",
        model=load_model.make_handle("file"),
        acquisition_function="PosteriorStandardDeviation",
        client=client,
        number_of_points=1,
    )
    recommend_graph.add_node(recommend)

    output_rec_points = recommend.make_handle("recommended_points")
    output_acq_value = recommend.make_handle("acquisition_function_value")

    display = Node(
        node_name="Display",
        label="Display",
        value=output_rec_points,
        client=client,
    )
    recommend_graph.add_node(display)

    # Wrap the graph in a workflow node
    recommend_workflow = Workflow(
        graph=recommend_graph.nodes,
        inputs=recommend_graph.external_input,
        external_input_id=recommend_graph.external_input_id,
        requested_output={
            "RecommendedPoints": output_rec_points.model_dump(),
            "AcquisitionFunctionValue": output_acq_value.model_dump(),
        },
        client=client,
    )
    rec_response = client.run_node(recommend_workflow)
    assert rec_response.status.value == "completed"

    rec_points = float(rec_response.progress["Display"].outputs["value"].split("\n")[1])
    return rec_points


def train_recommend(x, y):

    iter_idx = int(os.environ["MATFLOW_ELEMENT_ITER_IDX"])
    print(f"{iter_idx=!r}")

    x_train = x
    y_train = y

    # Set up the client
    client = Client()
    client.authenticate()

    project_name = "Personal"
    project_id = client.projects.get_project_id_by_name(project_name)

    pd.Series(x_train).to_csv("x_train.csv", index=False, header=False)
    pd.Series(y_train).to_csv("y_train.csv", index=False, header=False)
    x_train_ID = upload_dataset(
        client, f"x_train_{iter_idx}.csv", "x_train.csv", project_id
    )
    y_train_ID = upload_dataset(
        client, f"y_train_{iter_idx}.csv", "y_train.csv", project_id
    )

    model_ID = train_model(client, project_id, x_train_ID, y_train_ID, iter_idx)
    y_pred, y_std = predict(client, project_id, model_ID, iter_idx)

    plot_model_uncertainty(
        training_dpa=download_dataset(client, f"x_train_{iter_idx}.csv", project_id),
        training_fs=download_dataset(client, f"y_train_{iter_idx}.csv", project_id),
        visualise_means=download_dataset(client, f"mean_{iter_idx}", project_id),
        visualise_stds=download_dataset(client, f"std_{iter_idx}", project_id),
        visualise_inputs=download_dataset(
            client, f"visualise_inputs_{iter_idx}", project_id
        ),
    )

    rec_point = recommend_next_x(client, project_id, model_ID)

    x = np.hstack([x, rec_point])
    return {"x": x}
