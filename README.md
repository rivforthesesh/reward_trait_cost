# reward_trait_cost
Change the cost of every trait available in the reward store, **including modded content!** 

## How to Use
Make sure you have enabled mods in game.

When you first run the game with this mod, a file called "riv_reward_trait_cost.cfg" will be created in the same folder as the .ts4script, if it doesn't already exist.

You can configure all reward trait costs with two variables - the multiplier `m` and the added `a`.

To get the new cost, the game will take the original cost, multiply it by `m`, round up, and then add `a`:

`new_cost = ceil(m * cost) + a`

`m` and `a` can be changed by editing the .cfg file directly (the easiest way, since you don't need to bother coming back here for commands!) or using cheat commands.

------------
For my source code and more details visit https://rivforthesesh.itch.io/rivs-reward-store-config

Please credit me if you use any of it!
