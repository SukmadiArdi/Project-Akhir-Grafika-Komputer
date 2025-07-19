# -*- coding: utf-8 -*-
"""
Aplikasi Grafika 3D Interaktif dengan PyOpenGL

Deskripsi:
Aplikasi ini mendemonstrasikan rendering objek 3D dengan PyOpenGL, dengan
kemampuan untuk mengimpor dan mengekspor model dari/ke format file .obj.
Versi ini memperbaiki masalah pivot rotasi dan shading pada model yang diimpor.

Fitur Utama:
- Import/Export: Memuat model .obj (I) dan menyimpan model .obj (O).
- Transformasi Akurat: Rotasi terjadi pada pusat geometris objek.
- Shading Akurat: Pencahayaan halus (smooth shading) dengan data normal
  yang dipertahankan saat import/export.
- Transformasi Interaktif: Rotasi, Translasi, Zoom/Skala.
- Pemilihan Warna: Tombol angka 1-5.
- Kamera Perspektif: Menggunakan gluPerspective dan gluLookAt.

Versi: 1.5
"""

# Import library yang diperlukan
import sys
import os
from math import sin, cos, radians

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
except ImportError:
    print("Error: PyOpenGL tidak terinstal.")
    print("Silakan instal dengan perintah: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

# =============================================================================
# 1. PENGELOLAAN STATE DAN VARIABEL GLOBAL
# =============================================================================

# Dimensi window
window_width = 1280
window_height = 720

# Variabel untuk transformasi objek
rotation_x = 0.0
rotation_y = 0.0
translate_x = 0.0
translate_y = 0.0
translate_z = 0.0  # Direset setiap load model
scale_factor = 1.0
object_color = [0.6, 0.7, 1.0]

# Variabel untuk interaksi mouse
mouse_down = False
last_mouse_x = 0
last_mouse_y = 0

# Struktur data untuk menyimpan model 3D yang dimuat
model = {
    "vertices": [],
    "normals": [],
    "faces": [],
    "center": (0.0, 0.0, 0.0)  # Pusat geometris model
}


# =============================================================================
# 2. FUNGSI IMPORT, EXPORT, DAN MANIPULASI MODEL
# =============================================================================

def center_model_and_reset_transform():
    """Menghitung pusat model, memindahkannya ke origin, dan mereset transformasi."""
    global model, rotation_x, rotation_y, translate_x, translate_y, translate_z, scale_factor
    if not model["vertices"]:
        return

    # Hitung bounding box
    min_x = min(v[0] for v in model["vertices"])
    max_x = max(v[0] for v in model["vertices"])
    min_y = min(v[1] for v in model["vertices"])
    max_y = max(v[1] for v in model["vertices"])
    min_z = min(v[2] for v in model["vertices"])
    max_z = max(v[2] for v in model["vertices"])

    # Hitung pusat geometris
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = (min_z + max_z) / 2.0
    model["center"] = (center_x, center_y, center_z)

    # Pindahkan semua vertex sehingga pusatnya ada di (0,0,0)
    new_vertices = []
    for v in model["vertices"]:
        new_vertices.append((v[0] - center_x, v[1] - center_y, v[2] - center_z))
    model["vertices"] = new_vertices

    # Hitung jarak terjauh dari origin untuk menentukan posisi kamera awal
    max_dist = max(max(abs(v[i]) for v in model["vertices"]) for i in range(3)) if model["vertices"] else 1

    # Reset transformasi
    rotation_x, rotation_y = 0.0, 0.0
    translate_x, translate_y = 0.0, 0.0
    # Atur translate_z agar objek terlihat sepenuhnya
    translate_z = -max_dist * 2.5
    scale_factor = 1.0
    print(f"Model dipusatkan di {model['center']}. Transformasi direset.")


def load_obj(filename):
    """Memuat model 3D dari sebuah file .obj."""
    global model
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' tidak ditemukan.")
        return

    temp_vertices, temp_normals, temp_faces = [], [], []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts: continue

            if parts[0] == 'v':
                temp_vertices.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'vn':
                temp_normals.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'f':
                face = []
                for part in parts[1:]:
                    indices = part.split('/')
                    v_idx = int(indices[0]) - 1
                    vn_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                    face.append((v_idx, vn_idx))
                temp_faces.append(tuple(face))

    model = {"vertices": temp_vertices, "normals": temp_normals, "faces": temp_faces}
    center_model_and_reset_transform()  # Pusatkan model setelah dimuat
    print(f"Model '{filename}' berhasil dimuat: {len(model['vertices'])} vertices, {len(model['faces'])} faces.")
    glutPostRedisplay()


def export_obj(filename):
    """Mengekspor model saat ini (dengan transformasi) ke file .obj."""
    if not model["vertices"]:
        print("Tidak ada model untuk diekspor.")
        return

    with open(filename, 'w') as f:
        f.write("# Diekspor oleh Aplikasi Grafika 3D \n")
        f.write(f"# Vertices: {len(model['vertices'])}\n")
        f.write(f"# Normals: {len(model['normals'])}\n")
        f.write(f"# Faces: {len(model['faces'])}\n\n")

        # Tulis semua vertex asli (sebelum transformasi)
        for v in model["vertices"]:
            # Tambahkan kembali offset pusat sebelum menulis
            orig_v = (v[0] + model['center'][0], v[1] + model['center'][1], v[2] + model['center'][2])
            f.write(f"v {orig_v[0]:.6f} {orig_v[1]:.6f} {orig_v[2]:.6f}\n")
        f.write("\n")

        # Tulis semua normal asli
        for n in model["normals"]:
            f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
        f.write("\n")

        # Tulis semua face dengan format v//vn
        for face in model["faces"]:
            face_str = "f " + " ".join([f"{v_idx + 1}//{vn_idx + 1}" for v_idx, vn_idx in face])
            f.write(face_str + "\n")

    print(f"Model berhasil diekspor ke '{filename}' dengan data normal.")


def load_default_cube():
    """Memuat data kubus default ke dalam struktur model."""
    global model
    model = {
        "vertices": [
            (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
            (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
        ],
        "normals": [
            (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)
        ],
        "faces": [
            ((0, 0), (1, 0), (2, 0), (3, 0)),  # Belakang
            ((4, 1), (5, 1), (7, 1), (6, 1)),  # Depan
            ((0, 2), (4, 2), (6, 2), (3, 2)),  # Kanan
            ((1, 3), (5, 3), (7, 3), (2, 3)),  # Kiri
            ((1, 4), (5, 4), (4, 4), (0, 4)),  # Atas
            ((3, 5), (2, 5), (7, 5), (6, 5))  # Bawah
        ]
    }
    center_model_and_reset_transform()  # Pusatkan kubus juga


# =============================================================================
# 3. DOKUMENTASI DAN BANTUAN
# =============================================================================

def print_instructions():
    """Mencetak panduan penggunaan ke konsol."""
    print("=" * 60)
    print("      Aplikasi Grafika 3D Interaktif - PyOpenGL v1.5")
    print("=" * 60)
    print("--- FILE ---")
    print("  [I] Import File .obj (Ketik nama file di konsol)")
    print("  [O] Export File .obj (Ketik nama file di konsol)")
    print("\n--- KONTROL OBJEK ---")
    print("  Rotasi    : Klik kiri dan seret mouse")
    print("  Zoom      : Scroll mouse wheel")
    print("  Translasi : W, A, S, D")
    print("\n--- UBAH WARNA ---")
    print("  [1] Merah | [2] Hijau | [3] Biru | [4] Kuning | [5] Jingga | [6] Default")
    print("\n--- KONTROL APLIKASI ---")
    print("  Keluar    : Tekan tombol ESC")
    print("=" * 60)


# =============================================================================
# 4. FUNGSI MENGGAMBAR OBJEK
# =============================================================================

def draw_model():
    """Menggambar model yang saat ini dimuat dengan shading yang benar."""
    if not model["faces"]: return

    for face in model["faces"]:
        # Gambar sebagai triangles atau quads tergantung jumlah vertex
        if len(face) == 3:
            glBegin(GL_TRIANGLES)
        elif len(face) == 4:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_POLYGON)

        for v_idx, vn_idx in face:
            # Terapkan normal untuk SETIAP vertex untuk smooth shading
            if model["normals"] and vn_idx != -1:
                glNormal3fv(model["normals"][vn_idx])
            glVertex3fv(model["vertices"][v_idx])
        glEnd()


# =============================================================================
# 5. FUNGSI CALLBACK UTAMA OPENGL/GLUT
# =============================================================================

def display():
    """Fungsi display utama, dipanggil setiap kali layar perlu digambar ulang."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)

    light_position = [2.0, 3.0, 4.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    # Terapkan transformasi interaktif. Rotasi kini terjadi di sekitar (0,0,0)
    # karena modelnya sudah dipusatkan.
    glPushMatrix()  # Simpan matriks saat ini
    glTranslatef(translate_x, translate_y, translate_z)
    glRotatef(rotation_x, 1, 0, 0)
    glRotatef(rotation_y, 0, 1, 0)
    glScalef(scale_factor, scale_factor, scale_factor)

    glColor3fv(object_color)
    draw_model()
    glPopMatrix()  # Kembalikan matriks

    glutSwapBuffers()


def reshape(w, h):
    """Callback saat window diubah ukurannya."""
    global window_width, window_height
    window_width, window_height = w, h
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(w) / float(h), 0.1, 500.0)  # Perbesar zFar
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init():
    """Inisialisasi state OpenGL."""
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    # PERBAIKAN: Aktifkan normalisasi otomatis untuk vektor normal.
    # Ini memastikan pencahayaan tetap akurat bahkan setelah objek di-skala.
    glEnable(GL_NORMALIZE)

    light_ambient = [0.2, 0.2, 0.2, 1.0]
    light_diffuse = [1.0, 1.0, 1.0, 1.0]
    light_specular = [1.0, 1.0, 1.0, 1.0]
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

    mat_ambient = [0.7, 0.7, 0.7, 1.0]
    mat_diffuse = [0.8, 0.8, 0.8, 1.0]
    mat_specular = [1.0, 1.0, 1.0, 1.0]
    mat_shininess = [100.0]
    glMaterialfv(GL_FRONT, GL_AMBIENT, mat_ambient)
    glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_DIFFUSE)

    load_default_cube()
    print_instructions()


# =============================================================================
# 6. FUNGSI CALLBACK INPUT (MOUSE DAN KEYBOARD)
# =============================================================================

def keyboard(key, x, y):
    """Callback untuk input keyboard."""
    global translate_x, translate_y, scale_factor, object_color

    try:
        key_char = key.decode("utf-8").lower()
    except UnicodeDecodeError:
        return

    step = 0.2
    scale_step = 1.1

    if key == b'\x1b':
        print("Keluar dari aplikasi.")
        glutLeaveMainLoop()
    elif key_char == 'i':
        filename = input(">>> Masukkan nama file .obj untuk diimpor: ")
        load_obj(filename)
    elif key_char == 'o':
        filename = input(">>> Masukkan nama file .obj untuk diekspor: ")
        export_obj(filename)
    elif key_char == 'w':
        translate_y += step
    elif key_char == 's':
        translate_y -= step
    elif key_char == 'a':
        translate_x -= step
    elif key_char == 'd':
        translate_x += step
    elif key_char in ['=', '+']:
        scale_factor *= scale_step
    elif key_char == '-':
        scale_factor /= scale_step
    elif key_char == '1':
        object_color = [1.0, 0.3, 0.3]; print("Warna: Merah")
    elif key_char == '2':
        object_color = [0.3, 1.0, 0.3]; print("Warna: Hijau")
    elif key_char == '3':
        object_color = [0.3, 0.3, 1.0]; print("Warna: Biru")
    elif key_char == '4':
        object_color = [1.0, 1.0, 0.3]; print("Warna: Kuning")
    elif key_char == '5':
        object_color = [1.0, 0.3, 1.0]; print("Warna: Jingga")
    elif key_char == '6':
        object_color = [0.6, 0.7, 1.0]; print("Warna: Biru Muda (Default)")
    glutPostRedisplay()


def mouse_click(button, state, x, y):
    """Callback untuk klik mouse (rotasi)."""
    global mouse_down, last_mouse_x, last_mouse_y
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_down = True
            last_mouse_x, last_mouse_y = x, y
        elif state == GLUT_UP:
            mouse_down = False


def mouse_motion(x, y):
    """Callback untuk gerakan mouse (rotasi)."""
    global rotation_x, rotation_y, last_mouse_x, last_mouse_y
    if mouse_down:
        dx, dy = x - last_mouse_x, y - last_mouse_y
        rotation_y += dx * 0.5
        rotation_x += dy * 0.5
        last_mouse_x, last_mouse_y = x, y
        glutPostRedisplay()


def mouse_wheel(wheel, direction, x, y):
    """Callback untuk scroll mouse (zoom/skala)."""
    global scale_factor
    scale_step = 1.1
    if direction > 0:
        scale_factor *= scale_step
    elif direction < 0:
        scale_factor /= scale_step
    glutPostRedisplay()


# =============================================================================
# 7. FUNGSI MAIN
# =============================================================================

def main():
    """Fungsi utama untuk menginisialisasi GLUT dan memulai loop."""
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Aplikasi Grafika 3D Interaktif - OpenGL")

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse_click)
    glutMotionFunc(mouse_motion)
    glutMouseWheelFunc(mouse_wheel)

    init()
    glutMainLoop()


if __name__ == "__main__":
    main()
