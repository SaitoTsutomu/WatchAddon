import os
from datetime import datetime
from pathlib import Path

import bpy

bl_info = {
    "name": "WatchFile",
    "author": "tsutomu",
    "version": (0, 1),
    "blender": (3, 1, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Sidebar > Edit Tab",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/WatchFile",  # ドキュメントURL
}


class CWF_OT_watch_file(bpy.types.Operator):
    bl_idname = "object.watch_file"
    bl_label = "Watch"
    bl_description = "Execute a file when modified."

    file: bpy.props.StringProperty()  # type: ignore
    _timer = None  # インスタンスが異なることがあるので、代入はクラスにすること
    _path = None  # インスタンスが異なることがあるので、代入はクラスにすること
    _last = None  # インスタンスが異なることがあるので、代入はクラスにすること

    def execfile(self):
        if (t := self._path.stat().st_mtime) > self._last:
            self.__class__._last = t
            exec(self._path.read_text())
            print(f"{datetime.now()} execute {self.file}")

    def stop(self, context):
        if self._timer:
            # タイマの登録を解除
            context.window_manager.event_timer_remove(self._timer)
            self.__class__._timer = None

    def modal(self, context, event):
        if event.type == "TIMER":
            if not self._path.exists():
                return {"CANCELLED"}
            self.execfile()
        return {"PASS_THROUGH"} if self._timer else {"FINISHED"}

    def invoke(self, context, event):
        if context.area.type != "VIEW_3D":
            return {"CANCELLED"}
        if not self._timer:
            self.__class__._path = Path(self.file)
            if self._path.exists():
                self.__class__._last = -1
                self.execfile()
                # タイマを登録
                timer = context.window_manager.event_timer_add(1, window=context.window)
                self.__class__._timer = timer
                context.window_manager.modal_handler_add(self)
                # モーダルモードへの移行
                return {"RUNNING_MODAL"}
        self.stop(context)
        # モーダルモードを終了
        return {"FINISHED"}


class CWF_PT_watch_file(bpy.types.Panel):
    bl_label = "WatchFile"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        self.layout.prop(context.scene, "file")
        text, icon = "Start", "PLAY"
        if CWF_OT_watch_file._timer:
            text, icon = "Pause", "PAUSE"
        prop = self.layout.operator(CWF_OT_watch_file.bl_idname, text=text, icon=icon)
        prop.file = context.scene.file


classes = [
    CWF_OT_watch_file,
    CWF_PT_watch_file,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.file = bpy.props.StringProperty(default=os.getenv("WATCH_FILE", ""))


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.file


if __name__ == "__main__":
    register()
