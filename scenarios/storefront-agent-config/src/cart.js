// A tiny, real piece of the fictional storefront so the repository reads
// like a project, not a test file.
export function cartTotal(items) {
  return items.reduce((total, item) => total + item.price * item.quantity, 0);
}
