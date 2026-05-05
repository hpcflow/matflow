import numpy as np

from matflow.param_classes.utils import masked_array_from_list


def test_masked_array_from_list_1D():
    arr_lst = [1, 2, 3]
    assert np.allclose(masked_array_from_list(arr_lst), np.array(arr_lst))


def test_masked_array_from_list_2D():
    arr_lst = [[1, 2, 3], [4, 5, 6]]
    assert np.allclose(masked_array_from_list(arr_lst), np.array(arr_lst))


def test_masked_array_from_list_1D_masked():
    arr_lst = [1, 2, "x"]
    expected_data = np.array([1, 2, -1])
    expected_mask = np.array([0, 0, 1])
    expected = np.ma.masked_array(data=expected_data, mask=expected_mask)
    assert np.allclose(masked_array_from_list(arr_lst), expected)


def test_masked_array_from_list_2D_masked():
    arr_lst = [
        [1, 2, "x"],
        [3, 4, "x"],
        [5, 6, "x"],
    ]
    expected_data = np.array(
        [
            [1, 2, -1],
            [3, 4, -1],
            [5, 6, -1],
        ]
    )
    expected_mask = np.array(
        [
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
        ]
    )
    expected = np.ma.masked_array(data=expected_data, mask=expected_mask)
    assert np.allclose(masked_array_from_list(arr_lst), expected)
