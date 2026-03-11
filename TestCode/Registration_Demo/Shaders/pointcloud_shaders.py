# Shader code for rendering the pointcloud
POINT_VERTEX_SHADER = """#version 400 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;

out vec3 vertColor;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    vertColor = color;
}"""

POINT_FRAGMENT_SHADER = """#version 400 core
in vec3 vertColor;
out vec4 fragColor;

void main() {
    fragColor = vec4(vertColor, 1.0);
}"""