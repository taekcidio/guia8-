const $ = (selector) => document.querySelector(selector);
const money = (amount) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(amount);

let products = [];

async function api(path, options) {
  const response = await fetch(path, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("No pudimos leer la respuesta de la tienda.");
  }
  if (!response.ok) {
    throw new Error(payload.error || "No fue posible completar la solicitud.");
  }
  return payload;
}

function showMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("is-error", isError);
}

function renderProducts() {
  const query = $("#search").value.trim().toLocaleLowerCase("es");
  const category = $("#category-filter").value;
  const filtered = products.filter((product) => {
    const matchesName = product.name.toLocaleLowerCase("es").includes(query);
    return matchesName && (!category || product.category === category);
  });

  $("#product-count").textContent =
    filtered.length === 1 ? "1 producto" : `${filtered.length} productos`;
  $("#catalog-empty").hidden = filtered.length !== 0;
  $("#products").replaceChildren(
    ...filtered.map((product) => {
      const card = document.createElement("article");
      card.className = "product-card";

      const photo = document.createElement("div");
      photo.className = "product-photo";
      const image = document.createElement("img");
      image.src = product.image;
      image.alt = product.image_alt || product.name;
      image.loading = "lazy";
      image.decoding = "async";
      photo.append(image);

      const availability = document.createElement("span");
      availability.className = `availability${product.stock === 0 ? " sold-out" : ""}`;
      availability.textContent =
        product.stock === 0 ? "Agotado" : `${product.stock} disponibles`;
      photo.append(availability);

      const details = document.createElement("div");
      details.className = "product-details";
      const categoryLabel = document.createElement("p");
      categoryLabel.className = "product-category";
      categoryLabel.textContent = product.category;
      const name = document.createElement("h3");
      name.textContent = product.name;
      const description = document.createElement("p");
      description.className = "product-description";
      description.textContent = product.description;
      const price = document.createElement("p");
      price.className = "product-price";
      price.textContent = money(product.price);
      details.append(categoryLabel, name, description, price);
      card.append(photo, details);
      return card;
    }),
  );
}

function renderUsers(users, preferredId = "") {
  const select = $("#users");
  const previous = preferredId || select.value;
  const placeholder = new Option(
    users.length ? "Selecciona tu cuenta" : "Primero crea una cuenta",
    "",
  );
  select.replaceChildren(placeholder);
  for (const user of users) {
    select.add(new Option(user.name, user.id));
  }
  if (previous && users.some((user) => String(user.id) === String(previous))) {
    select.value = String(previous);
  }
  select.disabled = users.length === 0;
}

function renderProductOptions() {
  const select = $("#product-options");
  const previous = select.value;
  select.replaceChildren(new Option("Selecciona un producto", ""));
  for (const product of products) {
    const option = new Option(
      product.stock > 0
        ? `${product.name} · ${money(product.price)}`
        : `${product.name} · Agotado`,
      product.id,
    );
    option.disabled = product.stock === 0;
    select.add(option);
  }
  if (
    previous &&
    products.some(
      (product) => String(product.id) === previous && product.stock > 0,
    )
  ) {
    select.value = previous;
  }
  select.disabled = products.every((product) => product.stock === 0);
  updateQuantityLimit();
}

function updateQuantityLimit() {
  const product = products.find(
    (item) => String(item.id) === $("#product-options").value,
  );
  const quantity = $("#quantity");
  const hint = $("#stock-hint");
  if (!product) {
    quantity.removeAttribute("max");
    quantity.value = "1";
    quantity.disabled = true;
    hint.textContent = "";
    return;
  }
  quantity.disabled = product.stock === 0;
  quantity.max = String(product.stock);
  quantity.value = String(Math.min(Math.max(Number(quantity.value) || 1, 1), product.stock));
  hint.textContent =
    product.stock === 1 ? "1 disponible" : `${product.stock} disponibles`;
}

function formatDate(value) {
  const date = new Date(`${value.replace(" ", "T")}Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function renderOrders(orders) {
  const container = $("#orders");
  if (orders.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-orders";
    empty.textContent = "Aún no hay pedidos. Cuando registres uno, aparecerá aquí.";
    container.replaceChildren(empty);
    return;
  }

  const table = document.createElement("table");
  table.className = "orders-table";
  const headings = ["Fecha", "Usuario", "Producto", "Cantidad", "Total", "Estado"];
  const head = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const heading of headings) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = heading;
    headerRow.append(cell);
  }
  head.append(headerRow);

  const body = document.createElement("tbody");
  for (const order of orders) {
    const row = document.createElement("tr");
    const productNames = order.items.map((item) => item.product_name).join(", ");
    const quantity = order.items
      .map((item) => `${item.quantity} ${item.quantity === 1 ? "unidad" : "unidades"}`)
      .join(", ");
    const values = [
      formatDate(order.created_at),
      order.user_name,
      productNames,
      quantity,
      money(order.total),
      order.status,
    ];
    for (const [index, value] of values.entries()) {
      const cell = document.createElement("td");
      if (index === 5) {
        const status = document.createElement("span");
        status.className = "order-status";
        status.textContent = value;
        cell.append(status);
      } else {
        cell.textContent = value;
      }
      if (index === 0) cell.dataset.label = "Fecha";
      if (index === 1) cell.dataset.label = "Usuario";
      if (index === 2) cell.dataset.label = "Producto";
      if (index === 3) cell.dataset.label = "Cantidad";
      if (index === 4) cell.dataset.label = "Total";
      if (index === 5) cell.dataset.label = "Estado";
      row.append(cell);
    }
    body.append(row);
  }
  table.append(head, body);
  container.replaceChildren(table);
}

async function refresh(preferredUserId = "") {
  const status = $("#status");
  try {
    const [health, productResponse, userResponse, orderResponse] =
      await Promise.all([
        api("/api/health"),
        api("/api/products"),
        api("/api/users"),
        api("/api/orders"),
      ]);
    products = productResponse.products;
    const categories = [...new Set(products.map((product) => product.category))];
    const categorySelect = $("#category-filter");
    const selectedCategory = categorySelect.value;
    categorySelect.replaceChildren(new Option("Todas las categorías", ""));
    for (const category of categories) {
      categorySelect.add(new Option(category, category));
    }
    if (categories.includes(selectedCategory)) {
      categorySelect.value = selectedCategory;
    }
    renderProducts();
    renderProductOptions();
    renderUsers(userResponse.users, preferredUserId);
    renderOrders(orderResponse.orders);
    status.textContent = health.status === "ok" ? "La tienda está lista" : "Tienda no disponible";
    status.classList.toggle("is-offline", health.status !== "ok");
    status.closest(".intro-note").classList.toggle("is-offline", health.status !== "ok");
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("is-offline");
    status.closest(".intro-note").classList.add("is-offline");
  }
}

$("#search").addEventListener("input", renderProducts);
$("#category-filter").addEventListener("change", renderProducts);
$("#product-options").addEventListener("change", updateQuantityLimit);
$("#quantity").addEventListener("change", updateQuantityLimit);

$("#user-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const message = $("#user-msg");
  button.disabled = true;
  showMessage(message, "");
  try {
    const result = await api("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    form.reset();
    await refresh(result.id);
    showMessage(message, `Cuenta creada. ¡Hola, ${result.name}!`);
  } catch (error) {
    showMessage(message, error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#order-submit");
  const message = $("#order-msg");
  button.disabled = true;
  showMessage(message, "");
  try {
    const result = await api("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: Number($("#users").value),
        items: [
          {
            product_id: Number($("#product-options").value),
            quantity: Number($("#quantity").value),
          },
        ],
      }),
    });
    showMessage(
      message,
      `Pedido #${result.id} registrado por ${money(result.total)}. Queda pendiente de pago.`,
    );
    await refresh();
  } catch (error) {
    showMessage(message, error.message, true);
    await refresh();
  } finally {
    button.disabled = false;
  }
});

$("#refresh").addEventListener("click", () => refresh());
refresh();
