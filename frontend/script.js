const API_BASE_URL = "https://scalable-product-browsing-backend.onrender.com/api/products";
let nextCursor = null; 
const limit = 12; 

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const searchInput = document.getElementById('searchInput');
const categorySelect = document.getElementById('categorySelect');
const searchBtn = document.getElementById('searchBtn');
const totalCountSpan = document.getElementById('totalCount');
const currentPageSpan = document.getElementById('currentPage');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const loadingDiv = document.getElementById('loading');

async function fetchProducts() {
    loadingDiv.classList.remove('hidden');
    productsGrid.innerHTML = '';

    const searchValue = searchInput.value.trim();
    const categoryValue = categorySelect.value;

    
    let url = `${API_BASE_URL}?limit=${limit}`;

    
    if (nextCursor) {
        url += `&cursor=${encodeURIComponent(nextCursor)}`;
    }

    
    if (searchValue) {
        url += `&search=${encodeURIComponent(searchValue)}`;
    }
    if (categoryValue) {
        url += `&category=${encodeURIComponent(categoryValue)}`;
    }

    try {
        const response = await fetch(url, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();

        
        
renderCards(data.results);

        
        nextCursor = data.next_cursor; 

        
        totalCountSpan.textContent = data.total;
        
        
        if (!nextCursor) {
            nextBtn.disabled = true; 
        } else {
            nextBtn.disabled = false;
        }

    } catch (error) {
        console.error("Error fetching data:", error);
    } finally {
        loadingDiv.classList.add('hidden');
    }
}
function renderCards(products) {
    if (!products || products.length === 0) {
        productsGrid.innerHTML = `<p class="col-span-full text-center text-gray-500 py-12">No products matched your criteria.</p>`;
        return;
    }

    productsGrid.innerHTML = products.map(product => `
        <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col justify-between border border-gray-100">
            <div class="p-5">
                <div class="text-xs font-bold uppercase tracking-wide text-blue-500 mb-1">${product.category}</div>
                <h3 class="text-base font-bold text-gray-900 mb-2 line-clamp-2">${product.name}</h3>
                <p class="text-xs text-gray-400">ID: #${product.id}</p>
            </div>
            <div class="px-5 pb-5 pt-2 flex items-center justify-between bg-gray-50 border-t border-gray-50">
                <span class="text-lg font-extrabold text-green-600">$${parseFloat(product.price).toFixed(2)}</span>
                <button class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-3 py-1.5 rounded-md transition shadow-sm">View details</button>
            </div>
        </div>
    `).join('');
}

function updatePaginationControls(total) {
    currentPageSpan.innerText = Math.floor(currentOffset / limit) + 1;
    prevBtn.disabled = currentOffset === 0;
    nextBtn.disabled = (currentOffset + limit) >= total;
}


// 1. Search Button Click Listener
searchBtn.addEventListener('click', () => {
    nextCursor = null; 
    fetchProducts();
});

// 2. Next Button Click Listener
nextBtn.addEventListener('click', () => {
    if (nextCursor) {
        fetchProducts(); 
    }
});

// 3. Category Dropdown Change Listener
categorySelect.addEventListener('change', () => {
    nextCursor = null; 
    fetchProducts();
});

fetchProducts();