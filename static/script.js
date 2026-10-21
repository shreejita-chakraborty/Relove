
const loginbtn = document.getElementById("loginbtn");
if (loginbtn) {
    loginbtn.addEventListener("click", function () {
        window.location.href = "/login";
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const searchBar = document.getElementById("search-bar");
    const sectionsToHide = [
        ".books-section-1",
        "#books-section-2",
        ".clothes-section-1",
        "#clothes-section-2",
        "footer"
    ];
    const productSections = [
        "#books-section-3",
        "#books-section-4",
        "#books-section-5"
    ];
    const products = document.querySelectorAll(
        "#books-section-3 .trending-items[data-title]"
    );
    const allProductSections = productSections
        .map(selector => document.querySelector(selector))
        .filter(Boolean);
    let selectedFilter = "";
    let filterType = "";
    function filterProducts() {
        const query = searchBar ? searchBar.value.trim().toLowerCase() : "";
        const filtering = query !== "" || selectedFilter !== "";
        sectionsToHide.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.style.display = filtering ? "none" : "";
            });
        });
        allProductSections.forEach(section => {
            section.style.display = filtering
                ? (section.id === "books-section-3" ? "" : "none")
                : "";
        });
        const trendingSection = document.querySelector("#books-section-3");
        if (trendingSection) {
            trendingSection.style.marginTop = filtering ? "100px" : "";

            const heading = trendingSection.querySelector("h1");
            if (heading) heading.style.display = filtering ? "none" : "";
        }
        products.forEach(product => {
            const title = (product.dataset.title ||
                product.querySelector(".clothing-name, .book-name")
                    ?.textContent || "").toLowerCase();

            const category = (product.dataset.genre || "").toLowerCase();
            const matchesSearch = title.includes(query);
            const matchesCategory =
                !selectedFilter || category === selectedFilter;
            product.style.display =
                matchesSearch && matchesCategory ? "" : "none";
        });
    }
    if (searchBar) {
        searchBar.addEventListener("input", filterProducts);
    }
    document.querySelectorAll(".genre-link").forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault();

            selectedFilter = (link.dataset.genre || "").toLowerCase();
            filterType = "books";

            document.querySelectorAll(".genre-link").forEach(item =>
                item.classList.remove("active")
            );
            link.classList.add("active");

            filterProducts();
        });
    });  
        document.querySelectorAll(".clothes-filter").forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault();

            selectedFilter = (link.dataset.filter || "").toLowerCase();
            filterType = "clothes";

            document.querySelectorAll(".clothes-filter").forEach(item =>
                item.classList.remove("active")
            );
            link.classList.add("active");
            filterProducts();
        });
    });
});