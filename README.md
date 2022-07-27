# Simple Dynamic Window Manager for Windows

https://user-images.githubusercontent.com/6392321/181370770-37652321-7905-40e5-bfd5-a033f7f5c04e.mp4

When I am working on a computer 99% of my interaction is using one of the following window configurations:
- A single fullscreen window (e.g. when I am coding, browsing the web, etc.)
- Two equal windows side-by-side (e.g. when debugging or when coding while reading documentation)

So the normal window managers waste a lot of bandwidth making all sorts of (to me) useless window configurations possible, this is an issue which tiling window managers tend to fix. On linux I normally use `i3` which is a decent (though not perfect) tiling window manager. The main feature that I miss in `i3` is the ability to have the same program on multiple workspaces, which is pretty useful for my use cases. For example sometimes I want to have a code editor and a browser side-by-side when reading documentation in a documentation workspace and once I am done with the documentation I want to move to a workspace with fullscreen code editor. (I am sure there is an extension or script that makes that possible, but at least it is not a first-class feature of `i3`). `dwm` is another window manager that does have a feature similar to this, however, as much as I enjoy being stuck in a boot-loop because I made a mistake in a "config" file, sometimes I need to actually get work done on my computer which seems to be the antithesis to `dwm`'s philosophy.

I have tried many tiling window managers on windows over the years, however, because windows's window manager is not really designed to be customized they all eventually led to frustrations that made me give up on them.

In this repository I try to create an *extremely* simple window manager for windows that tries to optimize my own use cases. The main idea is not to mess with window's window management as much as possible. Here is how it works: Whenever you run `window-manager.py`, it takes a snapshot of all open windows at the instance that you ran it and creates a dummy window. Whenever you focus on this window, instead of focusing the window, it restores all windows to the position and size that they were when the snapshot were taken. So for example for my use-case of having two configurations, one for reading documentation while coding and the other exclusively for coding, I can first create a snapshot when my code editor is full screen and then create another snapshot when editor and browser are snapped to different sides of the screen and toggle between these two configurations by focusing on these "dummy" windows. This method does not mess with windows' window management system at all and the system's behavior is completely indistinguishable from normal behavior except for when you focus on one of these dummy windows. Another advantage is that these windows can be controlled naturally using windows's normal window management shortcuts (e.g. control+tab) so your muscle memory is applicable.

Here is my setup:
* I use [autohotkey](https://www.autohotkey.com/) to lauch `window-manager.py` (I use `Win+Space` as the shortcut). Here is the script that I use:
```
#Space::
run pythonw C:\path\to\window-manager.py
return
```
* There is a textbox when you run `window-manager.py` where you can optionally enter a name for the dummy window. I use this name along with [switcheroo](https://github.com/kvakulo/Switcheroo) to quickly switch to a workspace by typing its name.
