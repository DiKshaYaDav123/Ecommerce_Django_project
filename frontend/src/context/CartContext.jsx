import { createContext, useContext, useEffect, useState } from "react";
import { authFetch, getAccessToken } from "../utils/auth";

const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const BASEURL = import.meta.env.VITE_DJANGO_BASE_URL;
  const [cartItems, setCartItems] = useState([]);
  const [total, setTotal] = useState(0);

  const fetchCart = async () => {
    const res = await authFetch(`${BASEURL}/api/cart/`);
    const data = await res.json();

    setCartItems(data.items || data.cart_items || []);
    setTotal(data.total || 0);
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const addToCart = async (productId) => {
    await authFetch(`${BASEURL}/api/cart/add/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId }),
    });
    fetchCart();
  };

  const updateQuantity = async (itemId, quantity) => {
    await authFetch(`${BASEURL}/api/cart/update/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId, quantity }),
    });
    fetchCart();
  };

  const removeFromCart = async (itemId) => {
    await authFetch(`${BASEURL}/api/cart/remove/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId }),
    });
    fetchCart();
  };

  const clearCart = () => {
    setCartItems([]);
    setTotal(0);
  }

  return (
    <CartContext.Provider value={{ cartItems, total, addToCart, updateQuantity, removeFromCart, clearCart }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
