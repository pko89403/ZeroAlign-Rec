// Food.com seed recipes. Each recipe is tagged against window.TAXONOMY.
// Field shape:
//   id, title, img, time (min), calories, cuisine,
//   dietary[], dish, meal, method, flavors[], effort, pop (0..1)

const R = (id, title, img, time, calories, cuisine, dietary, dish, meal, method, flavors, effort, pop) =>
  ({ id, title, img, time, calories, cuisine, dietary, dish, meal, method, flavors, effort, pop });

window.RECIPES = [
  R(101, "Miso-Glazed Salmon Rice Bowl",    "#e8b084",  25, 540, "Japanese",       ["pescatarian"],                                "bowl",      "dinner",    "seared",   ["umami","sweet"],             "weeknight",       0.88),
  R(102, "Tuscan White Bean Stew",          "#b9c39a",  45, 420, "Italian",        ["vegan","vegetarian"],                         "stew",      "dinner",    "stewed",   ["herbaceous","umami"],        "weeknight",       0.62),
  R(103, "Szechuan Dan Dan Noodles",        "#c25a3a",  30, 610, "Chinese",        ["omnivore"],                                   "noodles",   "dinner",    "simmered", ["spicy","umami"],             "weeknight",       0.81),
  R(104, "Lemon Ricotta Pancakes",          "#f3d9a4",  20, 480, "American",       ["vegetarian"],                                 "dessert",   "breakfast", "fried",    ["sweet","tangy"],             "quick",           0.74),
  R(105, "Harissa Roasted Cauliflower",     "#d4744a",  35, 320, "Moroccan",       ["vegan","vegetarian","gluten-free"],           "side",      "side",      "roasted",  ["spicy","smoky"],             "weeknight",       0.58),
  R(106, "Classic Beef Bourguignon",        "#8b4a2f", 180, 720, "French",         ["omnivore"],                                   "stew",      "dinner",    "stewed",   ["umami","rich"],              "slow-cook",       0.69),
  R(107, "Thai Green Curry with Tofu",      "#9bb67a",  35, 520, "Thai",           ["vegetarian","vegan"],                         "curry",     "dinner",    "simmered", ["spicy","creamy"],            "weeknight",       0.79),
  R(108, "Burrata & Heirloom Tomato Plate", "#e8a89a",  10, 380, "Italian",        ["vegetarian","gluten-free"],                   "appetizer", "lunch",     "raw",      ["fresh","creamy"],            "quick",           0.71),
  R(109, "Korean Kimchi Jjigae",            "#b83d2c",  40, 450, "Korean",         ["omnivore"],                                   "stew",      "dinner",    "stewed",   ["spicy","umami"],             "weeknight",       0.76),
  R(110, "Wild Mushroom Risotto",           "#c9a678",  40, 580, "Italian",        ["vegetarian","gluten-free"],                   "rice-dish", "dinner",    "simmered", ["umami","creamy"],            "weeknight",       0.84),
  R(111, "Shakshuka with Feta",             "#d86a3f",  25, 410, "Middle-Eastern", ["vegetarian"],                                 "stew",      "breakfast", "simmered", ["spicy","umami"],             "quick",           0.72),
  R(112, "Vietnamese Pho Bo",               "#a87c4f", 240, 540, "Vietnamese",     ["omnivore"],                                   "soup",      "dinner",    "simmered", ["umami","herbaceous"],        "slow-cook",       0.77),
  R(113, "Avocado Farro Grain Bowl",        "#a8b87a",  20, 460, "Californian",    ["vegetarian","vegan"],                         "bowl",      "lunch",     "no-cook",  ["fresh","herbaceous"],        "quick",           0.65),
  R(114, "Carne Asada Tacos",               "#c25e3a",  30, 580, "Mexican",        ["gluten-free","omnivore"],                     "wrap",      "dinner",    "grilled",  ["smoky","tangy"],             "weeknight",       0.86),
  R(115, "Dark Chocolate Olive Oil Cake",   "#5a3a2c",  55, 520, "Italian",        ["vegetarian"],                                 "dessert",   "dessert",   "baked",    ["sweet","rich"],              "weekend-project", 0.70),
  R(116, "Crispy Pork Banh Mi",             "#d89a5a",  45, 620, "Vietnamese",     ["omnivore"],                                   "sandwich",  "lunch",     "fried",    ["tangy","umami"],             "weeknight",       0.73),
  R(117, "Red Lentil Dal",                  "#e09a3a",  30, 340, "Indian",         ["vegan","vegetarian","gluten-free"],           "stew",      "dinner",    "simmered", ["spicy","creamy"],            "weeknight",       0.60),
  R(118, "Seared Scallops w/ Brown Butter", "#f0d9b4",  20, 380, "French",         ["pescatarian","gluten-free"],                  "appetizer", "dinner",    "seared",   ["umami","rich"],              "quick",           0.63),
  R(119, "Smashed Cucumber Salad",          "#7ba87a",  10, 120, "Chinese",        ["vegan","vegetarian","gluten-free"],           "salad",     "side",      "no-cook",  ["spicy","tangy","fresh"],     "quick",           0.55),
  R(120, "Sourdough Margherita Pizza",      "#d89a6a",  90, 680, "Italian",        ["vegetarian"],                                 "pizza",     "dinner",    "baked",    ["umami","fresh"],             "weekend-project", 0.89),
  R(121, "Spicy Peanut Soba Noodles",       "#c9834a",  20, 520, "Thai",           ["vegetarian","vegan"],                         "noodles",   "lunch",     "no-cook",  ["spicy","creamy"],            "quick",           0.68),
  R(122, "Roast Chicken with Lemon",        "#e0b47a",  75, 620, "French",         ["gluten-free","omnivore"],                     "roast",     "dinner",    "roasted",  ["herbaceous","umami"],        "weekend-project", 0.75),
  R(123, "Matcha Tiramisu",                 "#9bb07a",  60, 460, "Japanese",       ["vegetarian"],                                 "dessert",   "dessert",   "no-cook",  ["sweet","creamy"],            "weekend-project", 0.66),
  R(124, "Chickpea Shawarma Wrap",          "#d8a74a",  25, 480, "Middle-Eastern", ["vegan","vegetarian"],                         "wrap",      "lunch",     "roasted",  ["spicy","tangy"],             "quick",           0.61),
  R(125, "Creamy Tomato Pasta",             "#d87a5a",  25, 560, "Italian",        ["vegetarian"],                                 "pasta",     "dinner",    "simmered", ["creamy","umami"],            "weeknight",       0.82),
  R(126, "Japchae Glass Noodles",           "#b47a3a",  35, 500, "Korean",         ["vegetarian"],                                 "noodles",   "dinner",    "fried",    ["umami","sweet"],             "weeknight",       0.64),
];
