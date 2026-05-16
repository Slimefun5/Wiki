<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary>Table of Contents</summary>

- [How can I download / install Slimefun5 or its Addons?](#how-can-i-download--install-Slimefun5-or-its-addons)
- [Can I install Slimefun5 on a Singleplayer world?](#can-i-install-Slimefun5-on-a-singleplayer-world)
- [Will Slimefun5 be available for Minecraft version XYZ?](#will-Slimefun5-be-available-for-minecraft-version-xyz)
- [I have an error/bug with Slimefun5](#i-have-an-errorbug-with-Slimefun5)
- [What's the difference between the talisman and ender talisman?](#whats-the-difference-between-the-talisman-and-ender-talisman)
- [Can you stack Talismans?](#can-you-stack-talismans)
- [What can I do with stone chunks?](#what-can-i-do-with-stone-chunks)
- [How do I disable items per-world?](#how-do-i-disable-items-per-world)
- [How to disable all or individual researches?](#how-to-disable-all-or-individual-researches)
- [How much RAM does Slimefun5 use?](#how-much-ram-does-Slimefun5-use)
- [How does XYZ work?](#how-does-xyz-work)
- [How do I repair Slimefun5 items?](#how-do-i-repair-Slimefun5-items)
- [Can I enchant Slimefun5 items?](#can-i-enchant-Slimefun5-items)
- [How long does coolant last in reactors?](#how-long-does-coolant-last-in-reactors)
- [Is it Slimefun5 or Slimefun5](#is-it-Slimefun5-or-Slimefun5)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## How can I download / install Slimefun5 or its Addons?
To download and install Slimefun5 you can refer to [this guide here](https://github.com/Slimefun5/Slimefun5/wiki/Installing-Slimefun5).  
You can find Addons for Slimefun5 on our ["Addons" - page](https://github.com/Slimefun5/Slimefun5/wiki/Addons).<br>
You can install these just like you did with Slimefun5, putting them in the `/plugins/` folder of your Server.

## Can I install Slimefun5 on a Singleplayer world?
No.<br>
Slimefun5 is a Bukkit / Spigot plugin, so it requires you to have a Bukkit-based Minecraft Server running. Creating such a Server is very easy though, you will be able to find lots of tutorials online. If you want to enjoy Slimefun5 all on your own, set up a new Minecraft Server on your computer, install the plugin and connect to it using the address `localhost`. Without any extra efforts your server won't be visible to others outside of your local network anyway.

## Will Slimefun5 be available for Minecraft version XYZ?
Slimefun5 has been consistently available for every Minecraft version from MC 1.5 onwards, so I would say you can rest assured that it will come out for that Minecraft version too. With over 100+ contributors to the project, the chances are high someone is gonna update it to work with that version.

## I have an error/bug with Slimefun5
Ok, first things first, join our [Support Server](https://discord.gg/fsD4Bkh) if you aren't in it already and go to `#bug-discussions`. We need to determine if it is a bug, user error or intended behaviour. Note that we **do not accept bug reports on discord, only on GitHub**. But experience has shown that 9 of 10 "bugs" tend to be the result of really outdated plugin versions or similar, so please try to discuss these issues with others on our discord server first, so that developers can focus on confirmed bug reports.

Now, send us the following information (in the `#bug-discussions` channel):
1. Run /sf versions and send us a screenshot. We need the exact versions you are using, otherwise, we will not be able to help you.
"latest" is not helping us at all. So please run that command. (If you don't have access to this command then Shift-Right-Click your Slimefun5 Guide, you can find your versions in the uppermost middle slot.)

2. Check your console, are there any errors? (If so, then post them via https://pastebin.com/)

3. What do you intend to happen and what is happening?

Please also refer to [this page](https://github.com/Slimefun5/Slimefun5/wiki/How-to-report-bugs) for a much more in-depth guide on how to report issues.

Once you've sent us all this info then one of our staff or a community member will help you. **Do not ping any role or members**. If some time has passed (15+ mins) then you may ping the helpful role (`@Helpful`). Being impatient and pinging roles/members (**especially staff**) may get you warned or kicked.

## What's the difference between the talisman and ender talisman?
The Ender Talismans work even while in the Ender Chest however the normal [Talismans](https://github.com/Slimefun5/Slimefun5/wiki/Talismans) requires for it to be in your inventory.

## Can you stack Talismans?
Talismans by themselves are stackable items but having more than one Talisman of the same type will not increase their effects.<br>
However, some Talismans get consumed when you use them, so having multiple of these handy will last you longer obviously.

## What can I do with stone chunks?
4 Stone Chunks can be put into the [Compressor](https://github.com/Slimefun5/Slimefun5/wiki/Compressor) to craft one cobblestone.

## How do I disable items per-world?
You can disable items per-world by finding said world file in the folder `/plugins/Slimefun5/world-settings/` and by setting any item ID to false.

If you wish to disable **all** items in the world by setting `enabled` to false.

## How to disable all or individual researches?
You can disable all researching (All items are researched by default) by going to the research file `/plugins/Slimefun5/Researches.yml` and setting `enable-researching` to `false`

In the same research file, you can also disable specific researches or modify the cost of them. 

## How much RAM does Slimefun5 use?
You can't give an exact number or really even an estimate, we don't know your other plugins, addons, your server software, server version and we may even change things per-build which can affect RAM usage. We can recommend **at least** 4GB for any server though with or __without__ Slimefun5.

## How does XYZ work?
If you'd like to know how an item works please refer to [our wiki](https://github.com/Slimefun5/Slimefun5/wiki).
> **Note**: The Wiki is still missing pages and is community ran! If you can help add content then please refer to [this guide](https://github.com/Slimefun5/Slimefun5/wiki/Expanding-the-Wiki)

## How do I repair Slimefun5 items?
You will need to use the [Auto-Anvil](https://github.com/Slimefun5/Slimefun5/wiki/Auto-Anvil) and [Duct Tape](https://github.com/Slimefun5/Slimefun5/wiki/Miscellaneous-Items).

## Can I enchant Slimefun5 items?
You can only enchant an Item from Slimefun5 by using an [Auto-Enchanter](https://github.com/Slimefun5/Slimefun5/wiki/Auto-Enchanter).

## How long does coolant last in reactors?
Coolant lasts for 25 seconds no matter the type (normal or Nether Ice). Here is a table with the required amount of coolant per piece of fuel:
| Fuel            | Duration    | Coolant type | Coolant amount |
| --------------- | ----------- | ------------ | -------------- |
| Uranium         | 20m (1200s) | Normal       | 48             |
| Neptunium       | 10m (600s)  | Normal       | 24             |
| Boosted Uranium | 25m (1500s) | Normal       | 60             |
| Nether Star     | 30m (1800s) | Nether Ice   | 72             |

## Is it Slimefun5 or Slimefun5
It's Slimefun5, one day everyone will know the correct spelling... one day... maybe... who knows honestly.
