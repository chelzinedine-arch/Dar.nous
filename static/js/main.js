document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       MAP
    ========================= */

    const mapElement = document.getElementById("map");

    if (mapElement) {

        const map = L.map("map").setView(
            [30.4278, -9.5981],
            6
        );

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors"
            }
        ).addTo(map);


        /* Agadir */

        const agadir = L.marker(
            [30.4278, -9.5981]
        ).addTo(map);

        agadir.bindPopup(`
            <strong>Appartement à Agadir</strong><br>
            3 500 DH / mois<br>
            <a href="/property">Voir l'annonce</a>
        `);


        /* Marrakech */

        const marrakech = L.marker(
            [31.6295, -7.9811]
        ).addTo(map);

        marrakech.bindPopup(`
            <strong>Villa à Marrakech</strong><br>
            8 500 DH / mois<br>
            <a href="/property">Voir l'annonce</a>
        `);

    }


    /* =========================
       FAVORITES
    ========================= */

    const favoriteButtons =
        document.querySelectorAll(".favorite-btn");

    favoriteButtons.forEach(button => {

        button.addEventListener("click", () => {

            button.classList.toggle("active");

            if (button.classList.contains("active")) {
                button.textContent = "♥";
            } else {
                button.textContent = "♡";
            }

        });

    });


    /* =========================
       QUICK FILTERS
    ========================= */

    const filterButtons =
        document.querySelectorAll(".quick-filters button");

    filterButtons.forEach(button => {

        button.addEventListener("click", () => {

            const type = button.dataset.type;

            const cards =
                document.querySelectorAll(".property-card");

            cards.forEach(card => {

                if (
                    !type ||
                    card.dataset.type === type
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

        });

    });


    /* =========================
       SEARCH
    ========================= */

    const searchButton =
        document.getElementById("searchButton");

    if (searchButton) {

        searchButton.addEventListener("click", () => {

            const location =
                document
                    .getElementById("locationInput")
                    .value
                    .trim();

            const type =
                document
                    .getElementById("typeInput")
                    .value;

            const price =
                document
                    .getElementById("priceInput")
                    .value;

            const cards =
                document.querySelectorAll(".property-card");

            cards.forEach(card => {

                const city =
                    card.dataset.city;

                const cardType =
                    card.dataset.type;

                const cardPrice =
                    Number(card.dataset.price);

                const locationMatch =
                    !location ||
                    city
                        .toLowerCase()
                        .includes(location.toLowerCase());

                const typeMatch =
                    !type ||
                    cardType === type;

                const priceMatch =
                    !price ||
                    cardPrice <= Number(price);

                if (
                    locationMatch &&
                    typeMatch &&
                    priceMatch
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

        });

    }

});