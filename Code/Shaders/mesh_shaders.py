# Shader code for rendering mesh triangles
MESH_VERTEX_SHADER = """#version 400 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    fragPos = vec3(model * vec4(position, 1.0));
    fragNormal = mat3(transpose(inverse(model))) * normal;
}"""

MESH_FRAGMENT_SHADER = """#version 400 core
in vec3 fragNormal;
in vec3 fragPos;

out vec4 fragColor;

uniform vec3 meshColor;

void main() {
    // Simple Phong-like lighting
    vec3 normal = normalize(fragNormal);
    vec3 lightDir = normalize(vec3(1.0, -1.0, 1.0));
    
    float ambientStrength = 0.3;
    float diffuseStrength = max(dot(normal, lightDir), 0.0);
    
    vec3 ambient = ambientStrength * meshColor;
    vec3 diffuse = diffuseStrength * meshColor;
    
    fragColor = vec4(ambient + diffuse, 1.0);
}"""
