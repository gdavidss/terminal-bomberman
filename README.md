### Terminal Bomberman

```
🔴⬜⬛⬛⬛
⬜⬛⬜⬛⬛
⬜⬜⬜⬛💣
⬜⬛⬛⬛🔵
⬜⬜⬛⬜⬜
```




Run this game by calling ```python terminal.py```

Walk with WASD, put bomb by pressing F.

Hacked this quickly on a plane -- I've always been in love with bomberman and wanted to understand how to make it. The entire game is rendered on the terminal with emojis. 

There's support for NPCs and 2-person player, up to three players right now.

NPCs are implemented using A-star. There are two modes that the NPCs are always at: attack (coming closer to the player as much as it can and dropping a bomb) and defense (avoid dangerous paths based on simulating explosions).

