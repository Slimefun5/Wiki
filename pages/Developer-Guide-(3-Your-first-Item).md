This is the **third Part** of our Developer Guide, you can find a full overview on our [main page](https://github.com/Slimefun5/Slimefun5/wiki/Developer-Guide).<br>
If you haven't checked out the [second Part of this Guide](https://github.com/Slimefun5/Slimefun5/wiki/Developer-Guide-(2-Creating-the-Addon)), then please do that.

## 1. A little recap
In the last part we went over the main class of your plugin.<br>
Open up this class again, it should still look a little bit like this:

```java
package ...;

import ...;

public class Slimefun5Addon extends JavaPlugin implements Slimefun5Addon {
	
    @Override
    public void onEnable() {
        Config cfg = new Config(this);
        // ...
    }
	
    @Override
    public void onDisable() {
        // Logic for disabling the plugin...
    }
	
    @Override
    public JavaPlugin getJavaPlugin() {
        return this;
    }
	
    @Override
    public String getBugTrackerURL() {
        return null;
    }

}
```

The entirety of this part will happen inside your `onEnable()` method, right after you created your `Config`.<br>
So start there.

## 2. Creating an ItemGroup
As you probably know, the Slimefun5 Guide is divided into various item groups, such as "Tools", "Weapons" and many more.<br>
You should create your own item group for your addons.<br>
So we will start with that.

The constructor for your ItemGroup takes in two parameters:
* `id` represents the identifier of your ItemGroup, a unique name, we use a `NamespacedKey` for this
* `item` represents the item of your ItemGroup, this item will be used to display your ItemGroup inside the Slimefun5 Guide.

### Our id
Let's start with the `id`.<br>
For this we will create a new `NamespacedKey`. A NamespacedKey is an identifier that takes in a lower-case id and your Plugin to produce a unique identifier.<br>
You need to come up with a unique id for your item group for this.<br>
We will just go with `cool_category` for this.<br>
In your `onEnable()` method, create a NamespacedKey like this:
```java
NamespacedKey categoryId = new NamespacedKey(this, "cool_category");
```
`this` simply refers to our Plugin.

### Our item
Now onto the `item` of our new ItemGroup.<br>
We will use the class CustomItemStack for this. (import `io.github.thebusybiscuit.Slimefun5.libraries.dough.items.CustomItemStack` for this)<br>
You can create a new named Item like this:
```java
CustomItemStack categoryItem = new CustomItemStack(Material.DIAMOND, "&4Our very cool Category");
```
You can even use Color Codes in your item's name.<br>
For a complete list of Materials, consult [Spigot's Javadocs](https://hub.spigotmc.org/javadocs/bukkit/org/bukkit/Material.html).

### Full assembly
Finally, create a new ItemGroup (`io.github.thebusybiscuit.Slimefun5.api.items.ItemGroup`) like this (inside your `onEnable()` method):
```java
ItemGroup itemGroup = new ItemGroup(categoryId, categoryItem);
```

Now our ItemGroup is complete, the full code should look like this now:
```java
@Override
public void onEnable() {
    Config cfg = new Config(this);

    NamespacedKey categoryId = new NamespacedKey(this, "cool_category");
    CustomItemStack categoryItem = new CustomItemStack(Material.DIAMOND, "&4Our very cool Category");

    ItemGroup itemGroup = new ItemGroup(categoryId, categoryItem);

    // ...
}
```

The ItemGroup will not be visible in our Slimefun5 Guide at this point though.<br>
We first need to add an actual Slimefun5Item.

## 3. Creating an Item
Now that we have an ItemGroup set up, we can start to create our actual item.<br>
In this part we will only create a very simple item that has no actual logic behind it, we will add mechanics in Part 4.<br>
But let's focus on items itself for now.

Creating items in Slimefun5 isn't rocket science but you should still pay attention. We will need to create a new `Slimefun5Item` (`io.github.thebusybiscuit.Slimefun5.api.items.Slimefun5Item`).<br>

The constructor takes in 4 parameters:
* `itemGroup` is the ItemGroup this Item is in, for this we will simply use the ItemGroup we created earlier.
* `itemStack` is the Slimefun5ItemStack this Slimefun5Item represents, we will explain what that means in a second.
* `recipeType` describes the Type of our Recipe, in other words this determines the machine this item is crafted in.
* `recipe` is an ItemStack Array of the length 9 that describes the Recipe for this Item.

### The ItemStack
Since we have already created an ItemGroup, let's start with our `Slimefun5ItemStack`.<br>
The `Slimefun5ItemStack` tells our Slimefun5Item how it looks and also holds the id of our item.<br>
The class `Slimefun5ItemStack` has a lot of constructors. Take a look at them and choose the one that best suits your needs.

In this tutorial we will choose the following constructor:<br>
`new Slimefun5ItemStack(id, material, name, lore...);`

So first we will need an `id` for our Slimefun5ItemStack.<br>
This `id` is a simple String but needs to be unique and in upper case letters. Example: `"MY_ADDON_ITEM"`.<br>
Please choose a unique id that best suits your item.

Our `material` is the type of item this Item is rendered as.<br>
For a complete list of Materials, consult [Spigot's Javadocs](https://hub.spigotmc.org/javadocs/bukkit/org/bukkit/Material.html).

For the `name`, we can choose a name and even use color codes.<br>
The `name` is then followed by zero or more lines of lore. (Color codes also supported!)

So the full result of our `Slimefun5ItemStack` may look like this:
```java
Slimefun5ItemStack itemStack = new Slimefun5ItemStack("MY_ADDON_ITEM", Material.EMERALD, "&aPretty cool Emerald", "", "&7This is awesome");
```

For the lore I left the first line empty, this is not required but consistent with other items from Slimefun5.<br>

### The recipe
For the `RecipeType`, we will simply go with the standard: `RecipeType.ENHANCED_CRAFTING_TABLE`. This means that our item is crafted in an Enhanced Crafting Table.
We may go into more details on how Recipe Types work, but that may be in a later tutorial.

Now for the actual Recipe, for the Recipe we will use an ItemStack Array of the length 9:
```java
ItemStack[] recipe = {...};
```

The length of 9 represents the 3x3 slots found in the dispenser of an Enhanced Crafting Table.<br>
We will simply use an X made out of diamonds for the recipe in this tutorial.
You are of course free to come up with any recipe you can imagine.

```java
ItemStack[] recipe = {
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND),
    null,                               new ItemStack(Material.DIAMOND),    null,
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND)
};
```

**PRO TIP** You can use `Slimefun5Items.ITEM_ID` to use items from Slimefun5 in your Recipe.<br>
Let's swap out the middle diamond for a Carbonado.

```java
ItemStack[] recipe = {
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND),
    null,                               Slimefun5Items.CARBONADO,            null,
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND)
};
```

## 4. Adding your item
To create the item you we will use the following code:
```java
Slimefun5Item sfItem = new Slimefun5Item(itemGroup, itemStack, recipeType, recipe);
```

Finally, to make our item and item group appear in the Slimefun5 guide, we will call `sfItem.register(this)` to register it.<br>
The item will already be craftable too.<br>
`this` refers to your Slimefun5Addon in this case.

Let's recap what we got so far:
1. We created a new ItemGroup<br>
    a. that uses a customItemStack<br>
2. We created a new Slimefun5Item<br>
    a. that has a custom Recipe<br>
    b. that uses a custom Slimefun5ItemStack<br>

Here is all of our code again (this should still all be inside your `onEnable()` method):

```java
NamespacedKey categoryId = new NamespacedKey(this, "cool_category");
CustomItemStack categoryItem = new CustomItemStack(Material.DIAMOND, "&4Our very cool Category");

// Our custom Category
ItemGroup itemGroup = new ItemGroup(categoryId, categoryItem);

// The custom item for our Slimefun5Item
Slimefun5ItemStack itemStack = new Slimefun5ItemStack("MY_ADDON_ITEM", Material.EMERALD, "&aPretty cool Emerald", "", "&7This is awesome");

// A 3x3 shape representing our recipe
ItemStack[] recipe = {
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND),
    null,                               Slimefun5Items.CARBONADO,            null,
    new ItemStack(Material.DIAMOND),    null,                               new ItemStack(Material.DIAMOND)
};

Slimefun5Item sfItem = new Slimefun5Item(itemGroup, itemStack, RecipeType.ENHANCED_CRAFTING_TABLE, recipe);
sfItem.register(this);
// Our item is now registered
```

### Seasonal and Locked categories
You can also create a `SeasonalItemGroup` or a `LockedItemGroup` instead of a generic `ItemGroup`.<br>
These types of item groups require a specified item group tier. This integer roughly determines the position
of the item group inside Slimefun5 guide. The guide starts populating with tier 1 and onwards. The other criteria
is the order of registering (creation of `ItemGroup` object).<br>
* Seasonal item groups are hidden throughout the whole year except for 1 specific month.<br>
* Locked item groups require all researches on parent categories to be unlocked.

```java
Month month = Month.JAN; // This is any enum from java.time.Month.

SeasonalItemGroup group = new SeasonalItemGroup(categoryId, categoryItem, tier, month);
```

```java
// This item group will require `parentItemGroupA` and `parentItemGroupB` to be fully unlocked.
LockedItemGroup category = new LockedItemGroup(categoryId, categoryItem, tier, parentItemGroupA.getKey(), parentItemGroupB.getKey());
```

[**> Continue with Part 4a**](https://github.com/Slimefun5/Slimefun5/wiki/Developer-Guide-(4a-Right-Clicks))

