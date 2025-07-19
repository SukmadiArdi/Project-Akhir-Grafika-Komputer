# -*- coding: utf-8 -*-
"""
Aplikasi Grafika 2D Interaktif dengan PyOpenGL

Deskripsi:
Aplikasi ini memungkinkan pengguna untuk menggambar objek 2D dasar, melakukan transformasi,
mengatur warna dan ketebalan, serta melakukan clipping.
Fitur utama yang telah diperbarui:
- Mode Seleksi: Klik objek, Shift+Klik, atau seret di area kosong.
- Pindahkan Objek: Klik dan tahan pada objek terpilih untuk menggesernya.
- Copy/Paste: Gunakan Ctrl+C dan Ctrl+V untuk duplikasi objek. (BUGFIXED)
- Manajemen Objek: Pilih Semua (Ctrl+A) dan Hapus Objek Terpilih (Delete).


Versi: 1.7.1
"""

# Import library yang diperlukan
import sys
import copy
from math import sin, cos, pi, sqrt, radians, degrees

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

# List untuk menyimpan semua objek yang digambar
objects = []
selected_indices = []
clipboard = []

# State aplikasi
current_mode = 'select'
is_drawing = False
is_dragging_selection = False
drag_last_pos = {'x': 0, 'y': 0}

# Atribut objek baru
current_color = (0.0, 0.0, 0.0)
current_thickness = 1.0

# Variabel sementara
temp_vertex = None
ghost_object = None
selection_box = None

# Definisi clipping window
clipping_window = {
    'xmin': 100, 'ymin': 100, 'xmax': 500, 'ymax': 400,
    'active': False,
    'color': (1.0, 0.0, 0.0),
}

# Konstanta Cohen-Sutherland
C_INSIDE, C_LEFT, C_RIGHT, C_BOTTOM, C_TOP = 0, 1, 2, 4, 8


# =============================================================================
# 2. DOKUMENTASI DAN BANTUAN
# =============================================================================

def print_instructions():
    """Mencetak panduan penggunaan ke konsol."""
    print("=" * 60)
    print("      Aplikasi Grafika 2D Interaktif - PyOpenGL v1.7.1")
    print("=" * 60)
    print("--- MODE ---")
    print("  [P] Titik | [L] Garis | [R] Persegi | [E] Elips | [F] Freehand")
    print("  [ESC] Kembali ke Mode Seleksi (Select)")
    print("\n--- SELEKSI & TRANSFORMASI ---")
    print("  Klik pada objek untuk memilih.")
    print("  Klik & Seret di area kosong untuk memilih beberapa objek.")
    print("  Klik & Tahan pada objek terpilih untuk menggesernya.")
    print("  [Shift+Klik] atau [Shift+Seret] untuk menambah/mengurangi objek.")
    print("  [Ctrl+A] untuk memilih semua objek.")
    print("  Gunakan Panah untuk Translasi, [Q/A] untuk Rotasi, [W/S] untuk Skala.")
    print("\n--- MANAJEMEN OBJEK ---")
    print("  [Ctrl+C] : Copy objek terpilih.")
    print("  [Ctrl+V] : Paste objek dari clipboard.")
    print("  [DELETE] / [BACKSPACE] : Hapus objek yang dipilih.")
    print("  [Shift+DELETE] : Hapus SEMUA objek (Clear All).")
    print("\n--- WARNA & KETEBALAN ---")
    print("  [1] Hitam | [2] Merah | [3] Hijau | [4] Biru")
    print("  [+/-] Ubah Ketebalan Garis")
    print("\n--- WINDOWING & CLIPPING ---")
    print("  [C] Buat Window (Klik & Seret) | [D] Nonaktifkan Window")
    print("  [G] Masuk mode Geser/Resize Window (Gunakan Panah / Shift+Panah)")
    print("=" * 60)


# =============================================================================
# 3. FUNGSI HELPER, MATEMATIKA, DAN ALGORITMA
# =============================================================================

def create_object(obj_type, vertices, color, thickness):
    """Membuat dictionary objek baru dan menambahkannya ke list."""
    global objects, selected_indices
    new_obj = {
        'type': obj_type,
        'vertices': vertices,
        'color': color,
        'thickness': thickness,
        'transform': {'translate': [0, 0], 'rotate': 0.0, 'scale': [1.0, 1.0]}
    }
    objects.append(new_obj)
    selected_indices = [len(objects) - 1]


def copy_selected_objects():
    """Menyalin objek terpilih ke clipboard."""
    global clipboard
    if not selected_indices:
        print("Tidak ada objek yang dipilih untuk di-copy.")
        return
    clipboard.clear()
    for index in selected_indices:
        clipboard.append(copy.deepcopy(objects[index]))
    print(f"{len(clipboard)} objek di-copy ke clipboard.")


def paste_objects():
    """Menempelkan objek dari clipboard."""
    global objects, selected_indices
    if not clipboard:
        print("Clipboard kosong.")
        return
    new_indices = []
    for obj_to_paste in clipboard:
        new_obj = copy.deepcopy(obj_to_paste)
        new_obj['transform']['translate'][0] += 15
        new_obj['transform']['translate'][1] += 15
        objects.append(new_obj)
        new_indices.append(len(objects) - 1)
    selected_indices = new_indices
    print(f"{len(new_indices)} objek di-paste.")
    glutPostRedisplay()


def delete_selected_objects():
    """Menghapus semua objek yang sedang dipilih."""
    global objects, selected_indices
    if not selected_indices: return
    print(f"Menghapus {len(selected_indices)} objek terpilih...")
    objects = [obj for i, obj in enumerate(objects) if i not in selected_indices]
    selected_indices.clear()
    glutPostRedisplay()


def clear_all():
    """Menghapus semua objek dari canvas."""
    global objects, selected_indices
    print("Menghapus semua objek...");
    objects.clear();
    selected_indices.clear();
    glutPostRedisplay()


def select_all():
    """Memilih semua objek di canvas."""
    global selected_indices
    selected_indices = list(range(len(objects)))
    print(f"Memilih semua ({len(selected_indices)}) objek.");
    glutPostRedisplay()


def get_object_center(obj):
    if not obj['vertices']: return (0, 0)
    if obj['type'] in ['point', 'ellipse', 'freehand']: return obj['vertices'][0]
    x_coords = [v[0] for v in obj['vertices']];
    y_coords = [v[1] for v in obj['vertices']]
    return (sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords))


def get_transformed_vertex(vertex, obj):
    center = get_object_center(obj);
    tr = obj['transform']
    vx, vy = vertex[0] - center[0], vertex[1] - center[1]
    vx, vy = vx * tr['scale'][0], vy * tr['scale'][1]
    angle_rad = radians(tr['rotate']);
    cos_a, sin_a = cos(angle_rad), sin(angle_rad)
    rvx = vx * cos_a - vy * sin_a;
    rvy = vx * sin_a + vy * cos_a
    final_x = rvx + center[0] + tr['translate'][0];
    final_y = rvy + center[1] + tr['translate'][1]
    return (final_x, final_y)


def get_object_aabb(obj):
    if not obj['vertices']: return None
    if obj['type'] == 'ellipse':
        center_x, center_y = obj['vertices'][0]
        rx = abs(obj['vertices'][1][0] - center_x);
        ry = abs(obj['vertices'][1][1] - center_y)
        verts_to_check = [(center_x + rx, center_y), (center_x - rx, center_y), (center_x, center_y + ry),
                          (center_x, center_y - ry)]
    else:
        verts_to_check = obj['vertices']
    transformed_verts = [get_transformed_vertex(v, obj) for v in verts_to_check]
    min_x = min(v[0] for v in transformed_verts);
    max_x = max(v[0] for v in transformed_verts)
    min_y = min(v[1] for v in transformed_verts);
    max_y = max(v[1] for v in transformed_verts)
    return (min_x, min_y, max_x, max_y)


def get_inverse_transformed_point(x, y, obj):
    center = get_object_center(obj);
    tr = obj['transform']
    px, py = x - tr['translate'][0], y - tr['translate'][1]
    px, py = px - center[0], py - center[1]
    angle_rad = radians(-tr['rotate']);
    cos_a, sin_a = cos(angle_rad), sin(angle_rad)
    rpx = px * cos_a - py * sin_a;
    rpy = px * sin_a + py * cos_a
    px, py = rpx, rpy
    sx = tr['scale'][0] if tr['scale'][0] != 0 else 1.0;
    sy = tr['scale'][1] if tr['scale'][1] != 0 else 1.0
    px, py = px / sx, py / sy
    final_px, final_py = px + center[0], py + center[1]
    return final_px, final_py


def dist_sq(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


def is_point_on_object(x, y, obj):
    ix, iy = get_inverse_transformed_point(x, y, obj)
    tolerance_sq = (obj['thickness'] * 3 + 3) ** 2
    obj_type, verts = obj['type'], obj['vertices']
    if obj_type == 'point':
        return dist_sq((ix, iy), verts[0]) < tolerance_sq * 2
    elif obj_type == 'line':
        p, v, w = (ix, iy), verts[0], verts[1];
        l2 = dist_sq(v, w)
        if l2 == 0: return dist_sq(p, v) < tolerance_sq
        t = max(0, min(1, ((p[0] - v[0]) * (w[0] - v[0]) + (p[1] - v[1]) * (w[1] - v[1])) / l2))
        proj = (v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1]))
        return dist_sq(p, proj) < tolerance_sq
    elif obj_type == 'rectangle':
        x_coords = sorted([verts[0][0], verts[1][0]]);
        y_coords = sorted([verts[0][1], verts[1][1]])
        return (x_coords[0] <= ix <= x_coords[1] and y_coords[0] <= iy <= y_coords[1])
    elif obj_type == 'ellipse':
        center = verts[0];
        rx, ry = abs(verts[1][0] - center[0]), abs(verts[1][1] - center[1])
        if rx == 0 or ry == 0: return False
        val = ((ix - center[0]) ** 2 / rx ** 2) + ((iy - center[1]) ** 2 / ry ** 2)
        return val <= 1.1
    elif obj_type == 'freehand':
        for i in range(len(verts) - 1):
            if is_point_on_object(x, y,
                                  {'type': 'line', 'vertices': [verts[i], verts[i + 1]], 'thickness': obj['thickness'],
                                   'transform': obj['transform']}):
                return True
    return False


def is_object_fully_inside_window(obj):
    if not obj['vertices']: return False
    aabb = get_object_aabb(obj)
    if not aabb: return False
    return (clipping_window['xmin'] <= aabb[0] and aabb[2] <= clipping_window['xmax'] and
            clipping_window['ymin'] <= aabb[1] and aabb[3] <= clipping_window['ymax'])


def compute_outcode(x, y):
    code = C_INSIDE
    if x < clipping_window['xmin']:
        code |= C_LEFT
    elif x > clipping_window['xmax']:
        code |= C_RIGHT
    if y < clipping_window['ymin']:
        code |= C_BOTTOM
    elif y > clipping_window['ymax']:
        code |= C_TOP
    return code


def cohen_sutherland_clip(x1, y1, x2, y2):
    outcode1, outcode2 = compute_outcode(x1, y1), compute_outcode(x2, y2)
    accept = False
    while True:
        if not (outcode1 | outcode2):
            accept = True; break
        elif (outcode1 & outcode2):
            break
        else:
            x, y = 0, 0
            outcode_out = outcode1 if outcode1 else outcode2
            if outcode_out & C_TOP:
                x = x1 + (x2 - x1) * (clipping_window['ymax'] - y1) / (y2 - y1); y = clipping_window['ymax']
            elif outcode_out & C_BOTTOM:
                x = x1 + (x2 - x1) * (clipping_window['ymin'] - y1) / (y2 - y1); y = clipping_window['ymin']
            elif outcode_out & C_RIGHT:
                y = y1 + (y2 - y1) * (clipping_window['xmax'] - x1) / (x2 - x1); x = clipping_window['xmax']
            elif outcode_out & C_LEFT:
                y = y1 + (y2 - y1) * (clipping_window['xmin'] - x1) / (x2 - x1); x = clipping_window['xmin']
            if outcode_out == outcode1:
                x1, y1 = x, y; outcode1 = compute_outcode(x1, y1)
            else:
                x2, y2 = x, y; outcode2 = compute_outcode(x2, y2)
    return (True, x1, y1, x2, y2) if accept else (False, 0, 0, 0, 0)


# =============================================================================
# 4. FUNGSI MENGGAMBAR OBJEK (HANYA VISUAL)
# =============================================================================

def draw_point(vertices, color, thickness):
    glPointSize(thickness * 5);
    glColor3fv(color);
    glBegin(GL_POINTS);
    glVertex2fv(vertices[0]);
    glEnd()


def draw_line(vertices, color, thickness, clip=False):
    x1, y1 = vertices[0];
    x2, y2 = vertices[1]
    if clip and clipping_window['active']:
        visible, nx1, ny1, nx2, ny2 = cohen_sutherland_clip(x1, y1, x2, y2)
        if not visible: return
        x1, y1, x2, y2 = nx1, ny1, nx2, ny2
    glLineWidth(thickness);
    glColor3fv(color);
    glBegin(GL_LINES);
    glVertex2f(x1, y1);
    glVertex2f(x2, y2);
    glEnd()


def draw_rectangle(vertices, color, thickness, clip=False):
    x1, y1 = vertices[0];
    x2, y2 = vertices[1]
    lines = [((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))]
    for line in lines: draw_line(line, color, thickness, clip)


def draw_ellipse(vertices, color, thickness, clip=False):
    center_x, center_y = vertices[0];
    rx = abs(vertices[1][0] - center_x);
    ry = abs(vertices[1][1] - center_y)
    num_segments = 100
    glLineWidth(thickness);
    glColor3fv(color);
    glBegin(GL_LINE_LOOP)
    for i in range(num_segments):
        theta = 2.0 * pi * i / num_segments
        x = rx * cos(theta) + center_x;
        y = ry * sin(theta) + center_y
        if clip and clipping_window['active'] and not (
                clipping_window['xmin'] <= x <= clipping_window['xmax'] and clipping_window['ymin'] <= y <=
                clipping_window['ymax']):
            glEnd();
            glBegin(GL_LINE_LOOP);
            continue
        glVertex2f(x, y)
    glEnd()


def draw_freehand(vertices, color, thickness, clip=False):
    glLineWidth(thickness);
    glColor3fv(color);
    glBegin(GL_LINE_STRIP)
    for v in vertices:
        if clip and clipping_window['active'] and not (
                clipping_window['xmin'] <= v[0] <= clipping_window['xmax'] and clipping_window['ymin'] <= v[1] <=
                clipping_window['ymax']):
            glEnd();
            glBegin(GL_LINE_STRIP);
            continue
        glVertex2fv(v)
    glEnd()


def draw_clipping_window():
    if clipping_window['active']:
        glEnable(GL_LINE_STIPPLE);
        glLineStipple(4, 0xAAAA);
        glColor3fv(clipping_window['color']);
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(clipping_window['xmin'], clipping_window['ymin']);
        glVertex2f(clipping_window['xmax'], clipping_window['ymin'])
        glVertex2f(clipping_window['xmax'], clipping_window['ymax']);
        glVertex2f(clipping_window['xmin'], clipping_window['ymax'])
        glEnd()
        glDisable(GL_LINE_STIPPLE)


def draw_selection_box():
    if selection_box:
        x1, y1, x2, y2 = selection_box
        glColor3f(0.3, 0.5, 0.9);
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1);
        glVertex2f(x2, y1);
        glVertex2f(x2, y2);
        glVertex2f(x1, y2)
        glEnd()
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.3, 0.5, 0.9, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1);
        glVertex2f(x2, y1);
        glVertex2f(x2, y2);
        glVertex2f(x1, y2)
        glEnd()
        glDisable(GL_BLEND)


# =============================================================================
# 5. FUNGSI CALLBACK UTAMA OPENGL/GLUT
# =============================================================================

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glLoadIdentity()
    for i, obj in enumerate(objects):
        display_color = obj['color']
        if i in selected_indices: display_color = (0.9, 0.5, 0.0)
        if clipping_window['active'] and is_object_fully_inside_window(obj): display_color = (0.1, 0.8, 0.2)
        glPushMatrix()
        center = get_object_center(obj)
        glTranslatef(obj['transform']['translate'][0], obj['transform']['translate'][1], 0)
        glTranslatef(center[0], center[1], 0)
        glRotatef(obj['transform']['rotate'], 0, 0, 1)
        glScalef(obj['transform']['scale'][0], obj['transform']['scale'][1], 1)
        glTranslatef(-center[0], -center[1], 0)
        obj_type = obj['type']
        if obj_type == 'point':
            draw_point(obj['vertices'], display_color, obj['thickness'])
        elif obj_type == 'line':
            draw_line(obj['vertices'], display_color, obj['thickness'], clip=True)
        elif obj_type == 'rectangle':
            draw_rectangle(obj['vertices'], display_color, obj['thickness'], clip=True)
        elif obj_type == 'ellipse':
            draw_ellipse(obj['vertices'], display_color, obj['thickness'], clip=True)
        elif obj_type == 'freehand':
            draw_freehand(obj['vertices'], display_color, obj['thickness'], clip=True)
        glPopMatrix()

    if is_drawing and ghost_object:
        obj = ghost_object;
        color = (0.5, 0.5, 0.5)
        if obj['type'] == 'draw_line':
            draw_line(obj['vertices'], color, obj['thickness'])
        elif obj['type'] == 'draw_rectangle':
            draw_rectangle(obj['vertices'], color, obj['thickness'])
        elif obj['type'] == 'draw_ellipse':
            draw_ellipse(obj['vertices'], color, obj['thickness'])
        elif obj['type'] == 'define_window':
            draw_rectangle(obj['vertices'], clipping_window['color'], 1.5)

    draw_clipping_window()
    draw_selection_box()
    glutSwapBuffers()


def reshape(w, h):
    global window_width, window_height
    window_width, window_height = w, h
    glViewport(0, 0, w, h if h > 0 else 1)
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(0.0, w, 0.0, h);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity()


def init():
    glClearColor(1.0, 1.0, 1.0, 1.0);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH);
    print_instructions()


# =============================================================================
# 6. FUNGSI CALLBACK INPUT (MOUSE DAN KEYBOARD)
# =============================================================================

def mouse_click(button, state, x, y):
    global current_mode, is_drawing, temp_vertex, ghost_object, selected_indices, selection_box
    global is_dragging_selection, drag_last_pos
    y = window_height - y

    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mods = glutGetModifiers()
            if current_mode == 'select':
                clicked_on_object = False
                for i in selected_indices:
                    if is_point_on_object(x, y, objects[i]):
                        is_dragging_selection = True
                        drag_last_pos = {'x': x, 'y': y}
                        clicked_on_object = True
                        break
                if not is_dragging_selection:
                    for i in range(len(objects) - 1, -1, -1):
                        if is_point_on_object(x, y, objects[i]):
                            if mods == GLUT_ACTIVE_SHIFT:
                                if i in selected_indices:
                                    selected_indices.remove(i)
                                else:
                                    selected_indices.append(i)
                            else:
                                selected_indices = [i]
                            clicked_on_object = True
                            break
                if not clicked_on_object:
                    is_drawing = True
                    selection_box = (x, y, x, y)
                    if mods != GLUT_ACTIVE_SHIFT:
                        selected_indices.clear()
            else:
                is_drawing = True;
                temp_vertex = (x, y)
                if current_mode == 'draw_point':
                    create_object('point', [(x, y)], current_color, current_thickness); is_drawing = False
                elif current_mode == 'draw_freehand':
                    create_object('freehand', [temp_vertex], current_color, current_thickness)
                elif current_mode in ['draw_line', 'draw_rectangle', 'draw_ellipse', 'define_window']:
                    ghost_object = {'type': current_mode, 'vertices': [temp_vertex, temp_vertex],
                                    'color': current_color, 'thickness': current_thickness}
        elif state == GLUT_UP:
            is_dragging_selection = False
            if selection_box:
                x1, y1, x2, y2 = selection_box
                sel_xmin, sel_xmax = min(x1, x2), max(x1, x2)
                sel_ymin, sel_ymax = min(y1, y2), max(y1, y2)
                newly_selected = set(selected_indices)
                for i, obj in enumerate(objects):
                    aabb = get_object_aabb(obj)
                    if aabb and not (
                            sel_xmax < aabb[0] or sel_xmin > aabb[2] or sel_ymax < aabb[1] or sel_ymin > aabb[3]):
                        newly_selected.add(i)
                selected_indices = list(newly_selected)
                print(f"{len(selected_indices)} objek terpilih.")
            if is_drawing and ghost_object:
                if current_mode in ['draw_line', 'draw_rectangle', 'draw_ellipse']:
                    create_object(ghost_object['type'].replace('draw_', ''), ghost_object['vertices'], current_color,
                                  current_thickness)
                elif current_mode == 'define_window':
                    vx = sorted([ghost_object['vertices'][0][0], ghost_object['vertices'][1][0]])
                    vy = sorted([ghost_object['vertices'][0][1], ghost_object['vertices'][1][1]])
                    clipping_window.update({'xmin': vx[0], 'ymin': vy[0], 'xmax': vx[1], 'ymax': vy[1], 'active': True})
                    print("Clipping window didefinisikan.");
                    current_mode = 'select'
            is_drawing = False;
            ghost_object = None;
            temp_vertex = None;
            selection_box = None
    glutPostRedisplay()


def mouse_motion(x, y):
    global selection_box, drag_last_pos
    y = window_height - y
    if is_dragging_selection:
        dx = x - drag_last_pos['x'];
        dy = y - drag_last_pos['y']
        for index in selected_indices:
            objects[index]['transform']['translate'][0] += dx
            objects[index]['transform']['translate'][1] += dy
        drag_last_pos = {'x': x, 'y': y}
        glutPostRedisplay()
        return
    if not is_drawing: return
    if selection_box:
        x1, y1, _, _ = selection_box
        selection_box = (x1, y1, x, y)
    elif current_mode == 'draw_freehand':
        if objects and objects[-1]['type'] == 'freehand': objects[-1]['vertices'].append((x, y))
    elif ghost_object and temp_vertex:
        ghost_object['vertices'][1] = (x, y)
    glutPostRedisplay()


def keyboard(key, x, y):
    global current_mode, current_color, current_thickness
    mods = glutGetModifiers()

    # --- PERBAIKAN: Cek byte code untuk shortcut Ctrl ---
    # Kode ini mendeteksi karakter kontrol ASCII yang dikirim saat Ctrl+key ditekan.
    if key == b'\x01':  # Ctrl+A
        select_all();
        return
    if key == b'\x03':  # Ctrl+C
        copy_selected_objects();
        return
    if key == b'\x16':  # Ctrl+V
        paste_objects();
        return

    if key == b'\x08' or key == b'\x7f':  # Backspace atau Delete
        if mods == GLUT_ACTIVE_SHIFT:
            clear_all()
        else:
            delete_selected_objects()
        return

    # Decode ke char setelah cek control keys
    try:
        key_char = key.decode("utf-8").lower()
    except UnicodeDecodeError:
        return  # Abaikan tombol yang tidak bisa di-decode

    modes = {'p': 'draw_point', 'l': 'draw_line', 'r': 'draw_rectangle', 'e': 'draw_ellipse', 'f': 'draw_freehand',
             'g': 'move_window'}
    # 'c' dipisah untuk menghindari konflik dengan Ctrl+C
    if key_char == 'c':
        current_mode = 'define_window'; print(f"Mode: define_window")
    elif key_char in modes:
        current_mode = modes[key_char]; print(f"Mode: {current_mode}")
    elif key == b'\x1b':
        current_mode = 'select'; print("Mode: Select")
    elif key_char == 'd':
        clipping_window['active'] = False; print("Clipping window dinonaktifkan.")
    elif key_char == '1':
        current_color = (0.0, 0.0, 0.0); print("Warna: Hitam")
    elif key_char == '2':
        current_color = (1.0, 0.0, 0.0); print("Warna: Merah")
    elif key_char == '3':
        current_color = (0.0, 1.0, 0.0); print("Warna: Hijau")
    elif key_char == '4':
        current_color = (0.0, 0.0, 1.0); print("Warna: Biru")
    elif key_char in ['+', '=']:
        current_thickness += 0.5; print(f"Ketebalan: {current_thickness}")
    elif key_char == '-':
        current_thickness = max(1.0, current_thickness - 0.5); print(f"Ketebalan: {current_thickness}")

    if selected_indices:
        for index in selected_indices:
            obj = objects[index]
            if key_char == 'q':
                obj['transform']['rotate'] += 5.0
            elif key_char == 'a':
                obj['transform']['rotate'] -= 5.0
            elif key_char == 'w':
                obj['transform']['scale'][0] *= 1.1; obj['transform']['scale'][1] *= 1.1
            elif key_char == 's':
                obj['transform']['scale'][0] *= 0.9; obj['transform']['scale'][1] *= 0.9
    glutPostRedisplay()


def special_keys(key, x, y):
    step = 5.0;
    mods = glutGetModifiers()
    if current_mode == 'select' and selected_indices:
        for index in selected_indices:
            transform = objects[index]['transform']['translate']
            if key == GLUT_KEY_UP:
                transform[1] += step
            elif key == GLUT_KEY_DOWN:
                transform[1] -= step
            elif key == GLUT_KEY_LEFT:
                transform[0] -= step
            elif key == GLUT_KEY_RIGHT:
                transform[0] += step
    elif current_mode == 'move_window' and clipping_window['active']:
        if mods == GLUT_ACTIVE_SHIFT:
            if key == GLUT_KEY_UP:
                clipping_window['ymax'] += step
            elif key == GLUT_KEY_DOWN:
                clipping_window['ymax'] -= step
            elif key == GLUT_KEY_LEFT:
                clipping_window['xmin'] -= step
            elif key == GLUT_KEY_RIGHT:
                clipping_window['xmax'] += step
        else:
            if key == GLUT_KEY_UP:
                clipping_window['ymin'] += step; clipping_window['ymax'] += step
            elif key == GLUT_KEY_DOWN:
                clipping_window['ymin'] -= step; clipping_window['ymax'] -= step
            elif key == GLUT_KEY_LEFT:
                clipping_window['xmin'] -= step; clipping_window['xmax'] -= step
            elif key == GLUT_KEY_RIGHT:
                clipping_window['xmin'] += step; clipping_window['xmax'] += step
    glutPostRedisplay()


# =============================================================================
# 7. FUNGSI MAIN
# =============================================================================

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Aplikasi Grafika 2D Interaktif - OpenGL v1.7.1")
    glutDisplayFunc(display);
    glutReshapeFunc(reshape);
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys);
    glutMouseFunc(mouse_click);
    glutMotionFunc(mouse_motion)
    init()
    glutMainLoop()


if __name__ == "__main__":
    main()
