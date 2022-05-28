import os
from datetime import datetime
from pathlib import Path
from subprocess import run

import bpy

bl_info = {
    "name": "WatchAddon",
    "author": "tsutomu",
    "version": (0, 1),
    "blender": (3, 1, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Sidebar > Edit Tab",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/WatchAddon",  # ドキュメントURL
}


class CWF_OT_watch_addon(bpy.types.Operator):
    bl_idname = "object.watch_addon"
    bl_label = "Watch"
    bl_description = "Re-activate addon when a file is modified."

    addon: bpy.props.StringProperty()  # type: ignore
    _timer = None  # インスタンスが異なることがあるので、代入はクラスにすること
    _path = None  # インスタンスが異なることがあるので、代入はクラスにすること
    _last = None  # インスタンスが異なることがあるので、代入はクラスにすること

    def off_on_addon(self):
        if (t := self._path.stat().st_mtime) > self._last:
            self.__class__._last = t
            bpy.ops.preferences.addon_disable(module=self.addon)
            bpy.ops.preferences.addon_enable(module=self.addon)
            print(f"{datetime.now()} execute {self.addon}")

    def stop(self, context):
        if self._timer:
            # タイマの登録を解除
            context.window_manager.event_timer_remove(self._timer)
            self.__class__._timer = None

    def modal(self, context, event):
        if event.type == "TIMER":
            if not self._path.exists():
                return {"CANCELLED"}
            self.off_on_addon()
        return {"PASS_THROUGH"} if self._timer else {"FINISHED"}

    def invoke(self, context, event):
        if context.area.type != "VIEW_3D":
            return {"CANCELLED"}
        if not self._timer:
            pth = Path(__file__).parent.parent / self.addon / "__init__.py"
            if not pth.exists():
                print(f"Not found {pth}")
                return {"CANCELLED"}
            else:
                run(["code", str(pth)])
                self.__class__._path = pth
                self.__class__._last = -1
                self.off_on_addon()
                # タイマを登録
                timer = context.window_manager.event_timer_add(1, window=context.window)
                self.__class__._timer = timer
                context.window_manager.modal_handler_add(self)
                # モーダルモードへの移行
                return {"RUNNING_MODAL"}
        self.stop(context)
        # モーダルモードを終了
        return {"FINISHED"}


class CWF_PT_watch_addon(bpy.types.Panel):
    bl_label = "WatchAddon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        self.layout.prop(context.scene, "addon")
        text, icon = "Start", "PLAY"
        if CWF_OT_watch_addon._timer:
            text, icon = "Pause", "PAUSE"
        prop = self.layout.operator(CWF_OT_watch_addon.bl_idname, text=text, icon=icon)
        prop.addon = context.scene.addon


classes = [
    CWF_OT_watch_addon,
    CWF_PT_watch_addon,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.addon = bpy.props.StringProperty()


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.addon


if __name__ == "__main__":
    register()
