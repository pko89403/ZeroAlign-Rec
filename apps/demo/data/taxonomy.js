// Master taxonomy — the vocabulary every downstream stage is guarded by.
// Values here are the ONLY strings that can appear in sketches / hard filters.

window.TAXONOMY = {
  cuisine: [
    "Italian", "Japanese", "Chinese", "Korean", "Thai", "Vietnamese",
    "Indian", "Mexican", "French", "American", "Middle-Eastern",
    "Moroccan", "Californian",
  ],
  dietary_style: [
    "vegetarian", "vegan", "gluten-free", "pescatarian", "dairy-free", "omnivore",
  ],
  dish_type: [
    "bowl", "soup", "stew", "noodles", "curry", "roast", "salad",
    "sandwich", "dessert", "pizza", "pasta", "rice-dish", "wrap", "appetizer",
  ],
  meal_type: [
    "breakfast", "brunch", "lunch", "dinner", "snack", "side", "dessert",
  ],
  cooking_method: [
    "roasted", "grilled", "stewed", "fried", "baked",
    "seared", "raw", "steamed", "simmered", "no-cook",
  ],
  flavor_profile: [
    "spicy", "sweet", "umami", "tangy", "herbaceous",
    "smoky", "creamy", "fresh", "rich",
  ],
  effort: [
    "quick", "weeknight", "weekend-project", "slow-cook",
  ],
};
