import math
import numpy as np

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader


VERTEX_SHADER_SRC = """
#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_color;

uniform mat4 u_mvp;
uniform float u_point_size;

out vec3 v_color;

void main()
{
    gl_Position = u_mvp * vec4(in_position, 1.0);
    gl_PointSize = u_point_size;
    v_color = in_color;
}
"""


FRAGMENT_SHADER_SRC = """
#version 330 core

in vec3 v_color;
out vec4 frag_color;

void main()
{
    frag_color = vec4(v_color, 1.0);
}
"""


def perspective(fovy_deg, aspect, z_near, z_far):
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    out = np.zeros((4, 4), dtype=np.float32)
    out[0, 0] = f / aspect
    out[1, 1] = f
    out[2, 2] = (z_far + z_near) / (z_near - z_far)
    out[2, 3] = (2.0 * z_far * z_near) / (z_near - z_far)
    out[3, 2] = -1.0
    return out


def normalize(v):
    n = np.linalg.norm(v)
    if n == 0:
        return v
    return v / n


def look_at(eye, center, up):
    f = normalize(center - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)

    out = np.eye(4, dtype=np.float32)
    out[0, 0:3] = s
    out[1, 0:3] = u
    out[2, 0:3] = -f
    out[0, 3] = -np.dot(s, eye)
    out[1, 3] = -np.dot(u, eye)
    out[2, 3] = np.dot(f, eye)
    return out


class GLViewer(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        self.setFormat(fmt)

        self.objects = []
        self.gpu_objects = []
        self.shader_program = None

        self.last_mouse_pos = QPoint()

        self.scene_center = np.zeros(3, dtype=np.float32)
        self.scene_radius = 1.0

        self.yaw_deg = 30.0
        self.pitch_deg = 20.0
        self.distance = 3.0
        self.pan = np.zeros(3, dtype=np.float32)

    def set_scene_objects(self, objects):
        self.objects = objects
        self._fit_view_to_scene()
        if self.isValid():
            self.makeCurrent()
            self._destroy_gpu_objects()
            self._upload_all_objects()
            self.doneCurrent()
        self.update()

    def _fit_view_to_scene(self):
        if not self.objects:
            self.scene_center = np.zeros(3, dtype=np.float32)
            self.scene_radius = 1.0
            self.distance = 3.0
            return

        mins = []
        maxs = []
        for obj in self.objects:
            if obj.positions.shape[0] == 0:
                continue
            mins.append(obj.positions.min(axis=0))
            maxs.append(obj.positions.max(axis=0))

        if not mins:
            self.scene_center = np.zeros(3, dtype=np.float32)
            self.scene_radius = 1.0
            self.distance = 3.0
            return

        mins = np.vstack(mins).min(axis=0)
        maxs = np.vstack(maxs).max(axis=0)

        self.scene_center = ((mins + maxs) * 0.5).astype(np.float32)
        extent = maxs - mins
        radius = 0.5 * float(np.linalg.norm(extent))
        self.scene_radius = max(radius, 1e-3)
        self.distance = max(3.0 * self.scene_radius, 1e-2)
        self.pan = np.zeros(3, dtype=np.float32)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glClearColor(0.08, 0.08, 0.10, 1.0)

        self.shader_program = compileProgram(
            compileShader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER),
        )

        self._upload_all_objects()

    def resizeGL(self, w, h):
        glViewport(0, 0, max(1, w), max(1, h))

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.shader_program is None:
            return

        glUseProgram(self.shader_program)

        mvp = self._compute_mvp_matrix()
        mvp_loc = glGetUniformLocation(self.shader_program, "u_mvp")
        point_size_loc = glGetUniformLocation(self.shader_program, "u_point_size")

        glUniformMatrix4fv(mvp_loc, 1, GL_TRUE, mvp)

        for gpu in self.gpu_objects:
            if not gpu["visible"] or gpu["count"] == 0:
                continue

            glUniform1f(point_size_loc, float(gpu["point_size"]))
            glBindVertexArray(gpu["vao"])
            glDrawArrays(GL_POINTS, 0, gpu["count"])

        glBindVertexArray(0)
        glUseProgram(0)

    def _compute_camera_vectors(self):
        yaw = math.radians(self.yaw_deg)
        pitch = math.radians(self.pitch_deg)

        direction = np.array(
            [
                math.cos(pitch) * math.cos(yaw),
                math.sin(pitch),
                math.cos(pitch) * math.sin(yaw),
            ],
            dtype=np.float32,
        )

        eye = self.scene_center + self.pan + direction * self.distance
        center = self.scene_center + self.pan
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return eye, center, up

    def _compute_mvp_matrix(self):
        aspect = max(1.0, self.width() / max(1.0, self.height()))
        proj = perspective(45.0, aspect, 0.001, max(1000.0 * self.scene_radius, 10.0))
        eye, center, up = self._compute_camera_vectors()
        view = look_at(eye, center, up)
        model = np.eye(4, dtype=np.float32)
        return proj @ view @ model

    def _upload_all_objects(self):
        self.gpu_objects = []
        for obj in self.objects:
            self.gpu_objects.append(self._upload_object(obj))

    def _upload_object(self, obj):
        positions = np.asarray(obj.positions, dtype=np.float32)
        colors = np.asarray(obj.colors, dtype=np.float32)

        if positions.shape[0] == 0:
            return {
                "vao": 0,
                "vbo": 0,
                "count": 0,
                "point_size": obj.point_size,
                "visible": obj.visible,
                "name": obj.name,
            }

        interleaved = np.hstack([positions, colors]).astype(np.float32, copy=False)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, interleaved.nbytes, interleaved, GL_STATIC_DRAW)

        stride = 6 * 4  # 6 float32 values

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        return {
            "vao": vao,
            "vbo": vbo,
            "count": positions.shape[0],
            "point_size": obj.point_size,
            "visible": obj.visible,
            "name": obj.name,
        }

    def _destroy_gpu_objects(self):
        for gpu in self.gpu_objects:
            vao = gpu.get("vao", 0)
            vbo = gpu.get("vbo", 0)

            if vao:
                glDeleteVertexArrays(1, [vao])
            if vbo:
                glDeleteBuffers(1, [vbo])

        self.gpu_objects = []

    def closeEvent(self, event):
        if self.isValid():
            self.makeCurrent()
            self._destroy_gpu_objects()
            if self.shader_program is not None:
                glDeleteProgram(self.shader_program)
                self.shader_program = None
            self.doneCurrent()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        dx = pos.x() - self.last_mouse_pos.x()
        dy = pos.y() - self.last_mouse_pos.y()

        if event.buttons() & Qt.LeftButton:
            self.yaw_deg += dx * 0.4
            self.pitch_deg += dy * 0.4
            self.pitch_deg = float(np.clip(self.pitch_deg, -89.0, 89.0))

        elif event.buttons() & Qt.RightButton:
            eye, center, up = self._compute_camera_vectors()
            forward = normalize(center - eye)
            right = normalize(np.cross(forward, up))
            true_up = normalize(np.cross(right, forward))

            pan_scale = self.scene_radius * 0.0025
            self.pan -= right * dx * pan_scale
            self.pan += true_up * dy * pan_scale

        self.last_mouse_pos = pos
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 0.9 if delta > 0 else 1.1
        self.distance *= zoom_factor
        self.distance = max(self.scene_radius * 0.05, self.distance)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._fit_view_to_scene()
            self.update()
        elif event.key() == Qt.Key_1 and len(self.gpu_objects) > 0:
            self.gpu_objects[0]["visible"] = not self.gpu_objects[0]["visible"]
            self.update()
        elif event.key() == Qt.Key_2 and len(self.gpu_objects) > 1:
            self.gpu_objects[1]["visible"] = not self.gpu_objects[1]["visible"]
            self.update()
        else:
            super().keyPressEvent(event)