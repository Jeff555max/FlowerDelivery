{% extends 'base.html' %}

{% block title %}Каталог{% endblock %}

{% block content %}
<h2 class="mb-4">Каталог цветов</h2>
<div class="row">
    {% for product in products %}
    <div class="col-md-4">
        <div class="card mb-4 shadow-sm">
            {% if product.image %}
            <img src="{{ product.image.url }}" class="card-img-top" alt="{{ product.name }}">
            {% endif %}
            <div class="card-body">
                <h5 class="card-title">{{ product.name }}</h5>
                <p class="card-text">{{ product.description }}</p>
                <p><strong>{{ product.price }} руб.</strong></p>

                <!-- Форма для выбора количества -->
                <div class="input-group mb-3">
                    <input type="number" id="quantity-{{ product.id }}" value="1" min="1" class="form-control">
                    <button class="btn btn-success" onclick="addToCart({{ product.id }})">Добавить в корзину</button>
                </div>
            </div>
        </div>
    </div>
    {% empty %}
    <p>Нет доступных товаров.</p>
    {% endfor %}
</div>

<!-- Место для сообщений -->
<div id="cart-message" class="alert alert-success mt-3 d-none"></div>

<!-- JavaScript -->
<script>
    function addToCart(productId) {
        let quantity = document.getElementById(`quantity-${productId}`).value;

        fetch(`/add_to_cart/${productId}/${quantity}/`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            let messageBox = document.getElementById('cart-message');
            messageBox.innerText = data.message;
            messageBox.classList.remove('d-none');

            setTimeout(() => {
                messageBox.classList.add('d-none');
            }, 3000);
        })
        .catch(error => console.error('Ошибка:', error));
    }
</script>
{% endblock %}
