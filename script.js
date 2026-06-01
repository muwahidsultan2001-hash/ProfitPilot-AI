async function searchProducts() {

    const keyword = document.getElementById("keyword").value;
    const resultsDiv = document.getElementById("results");
    const pipelineDiv = document.getElementById("pipeline");

    if (!keyword) {
        resultsDiv.innerHTML = "<p>Please enter a keyword</p>";
        return;
    }

    resultsDiv.innerHTML = "<p class='loading'>Searching real eBay deals...</p>";
    pipelineDiv.innerHTML = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ keyword })
        });

        const data = await response.json();

        // ❗ SAFETY CHECK (IMPORTANT FOR PRODUCTION)
        if (data.error) {
            resultsDiv.innerHTML = `<p style="color:red;">${data.error}</p>`;
            console.error("Backend error:", data);
            return;
        }

        const products = data.best_deals;

        // ---------------- PIPELINE ----------------
        if (data.pipeline) {
            pipelineDiv.innerHTML = `
                <div class="pipeline-box">
                    <h3>Pipeline Execution</h3>
                    <ul>
                        ${data.pipeline.map(step => `<li>${step}</li>`).join("")}
                    </ul>
                    <p><b>Total Results:</b> ${data.count}</p>
                </div>
            `;
        }

        resultsDiv.innerHTML = "";

        if (!products || products.length === 0) {
            resultsDiv.innerHTML = "<p>No profitable deals found</p>";
            return;
        }

        // ---------------- CARDS ----------------
        products.forEach(product => {

            const card = document.createElement("div");
            card.className = "card";

            card.innerHTML = `
                <h2>${product.title}</h2>

                <p>🔥 Sold: ${product.sold_count}</p>
                <p>💰 eBay Price: $${product.ebay_price}</p>
                <p>🏭 AliExpress Price: $${product.aliexpress_price}</p>
                <p>💸 Fees: $${product.fees}</p>

                <p class="profit">Profit: $${product.profit}</p>
                <p class="roi">ROI: ${product.roi}%</p>

                <a href="${product.url}" target="_blank">View on eBay</a>
            `;

            resultsDiv.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        resultsDiv.innerHTML = "<p style='color:red;'>Server error</p>";
    }
}