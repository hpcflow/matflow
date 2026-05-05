document.addEventListener("DOMContentLoaded", function () {
    const action_headings = document.querySelectorAll(".actions-heading");
    Array.from(action_headings).forEach(function (element) {
        element.addEventListener('click', function () {
            console.log("clicked!");
            this.parentElement.querySelector('table.action-table').classList.toggle("hidden");
            this.querySelector("span.action-hide-text").classList.toggle("hidden");
            this.querySelector("span.action-show-text").classList.toggle("hidden");
        });
    });

})
