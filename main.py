from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
import math

# =================================================
# DATA GLOBAL (TIDAK DIUBAH)
# =================================================
ringkasan = []
item_list = []
baris_per_item = []

jenis_armada = ""
total_baris = 0
total_muatan = 0
sisa_muatan = 0
total_baris_terpakai = 0
item_ke = 0

armada_index = None

# =================================================
# UTIL
# =================================================
def popup_info(judul, teks):
    Popup(
        title=judul,
        content=Label(text=teks),
        size_hint=(0.8, 0.3)
    ).open()

# =================================================
# UI
# =================================================
class ArmadaUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(6),
            spacing=dp(4),
            **kwargs
        )

        self.inputs = []

        self.add_widget(self.judul("ARMADA"))
        self.entry_armada = self.row("Jenis Armada", False)
        self.entry_baris = self.row("Total Baris", True)
        self.entry_muatan = self.row("Total Muatan", True)

        self.tombol_baris(
            ("Simpan", self.simpan_armada, (0.5, 0.8, 0.5, 1)),
            ("Reset", self.reset_armada, (1, 0.5, 0.5, 1))
        )

        self.add_widget(self.judul("ITEM"))
        self.entry_item = self.row("Nama Item", False)
        self.entry_karton = self.row("Jumlah Karton", True)
        self.entry_tambah = self.row("Isi Sebelum", True)
        self.entry_perbaris = self.row("Karton/Baris", True)

        self.tombol_baris(
            ("Proses", self.proses_item, (0.5, 0.7, 1, 1)),
            ("Reset", self.reset_item, (1, 0.9, 0.5, 1))
        )

        self.tombol_baris(
            ("Simpan", self.simpan_hasil, (0.6, 0.9, 0.6, 1)),
            ("Copy", self.copy_ringkasan, (0.7, 0.6, 0.9, 1)),
            ("RESET", self.reset_semua, (1, 0.4, 0.4, 1))
        )

        self.add_widget(self.judul("RINGKASAN"))

        # ===== PERBAIKAN SCROLL RINGKASAN (UI SAJA) =====
        self.text_hasil = TextInput(
            readonly=True,
            multiline=True,
            size_hint_y=None,
            font_size=dp(12),
            padding=dp(6)
        )

        self.text_hasil.bind(
            minimum_height=self.text_hasil.setter("height")
        )

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )
        scroll.add_widget(self.text_hasil)
        self.add_widget(scroll)

    # =================================================
    # BUILDER
    # =================================================
    def judul(self, teks):
        return Label(
            text=f"[b]{teks}[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(24),
            font_size=dp(20)
        )

    def row(self, label, angka):
        row = BoxLayout(size_hint_y=None, height=dp(32))
        row.add_widget(Label(text=label, size_hint_x=0.6, font_size=dp(18)))

        ti = TextInput(
            multiline=False,
            input_filter="int" if angka else None,
            size_hint_x=0.4,
            font_size=dp(18),
            padding=[dp(4), dp(6)]
        )

        ti.bind(on_text_validate=self.focus_next)
        ti.keyboard_on_key_down = self.key_down_wrapper(ti)

        self.inputs.append(ti)

        row.add_widget(ti)
        self.add_widget(row)
        return ti

    def tombol_baris(self, *data):
        row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        for teks, fungsi, warna in data:
            btn = Button(
                text=teks,
                font_size=dp(18),
                background_color=warna
            )
            btn.bind(on_press=fungsi)
            row.add_widget(btn)
        self.add_widget(row)

    # =================================================
    # KEYBOARD BEHAVIOR
    # =================================================
    def focus_next(self, instance):
        if instance in self.inputs:
            i = self.inputs.index(instance)
            if i + 1 < len(self.inputs):
                self.inputs[i + 1].focus = True

    def focus_prev(self, instance):
        if instance in self.inputs:
            i = self.inputs.index(instance)
            if i > 0:
                self.inputs[i - 1].focus = True

    def key_down_wrapper(self, widget):
        old = widget.keyboard_on_key_down

        def handler(window, keycode, text, modifiers):
            if keycode[1] == "backspace" and widget.text == "":
                self.focus_prev(widget)
                return True
            return old(window, keycode, text, modifiers)

        return handler

    # =================================================
    # LOGIKA (TIDAK DIUBAH)
    # =================================================
    def refresh_text(self):
        self.text_hasil.text = ""
        for r in ringkasan + item_list:
            self.text_hasil.text += r

    def simpan_armada(self, *_):
        global jenis_armada, total_baris, total_muatan, sisa_muatan, armada_index
        try:
            jenis_armada = self.entry_armada.text
            total_baris = int(self.entry_baris.text)
            total_muatan = int(self.entry_muatan.text)
        except:
            popup_info("Error", "Input harus angka")
            return

        sisa_muatan = total_muatan
        item_baru = []

        for teks in item_list:
            jumlah_item = 0
            for line in teks.splitlines():
                if " : " in line and not line.startswith("ITEM"):
                    try:
                        jumlah_item = int(line.split(":")[1])
                    except:
                        pass

            sisa_muatan -= jumlah_item

            baris = []
            for line in teks.splitlines():
                if line.startswith("Sisa muatan"):
                    baris.append(f"Sisa muatan  : {sisa_muatan}")
                else:
                    baris.append(line)

            item_baru.append("\n".join(baris) + "\n")

        item_list.clear()
        item_list.extend(item_baru)

        teks = (
            "\nARMADA\n"
            f"Jenis Armada : {jenis_armada}\n"
            f"Total Baris       : {total_baris}\n"
            f"Total Muatan  : {total_muatan}\n"
        )

        if armada_index is None:
            armada_index = len(ringkasan)
            ringkasan.append(teks)
        else:
            ringkasan[armada_index] = teks

        self.refresh_text()

    def reset_armada(self, *_):
        global armada_index, jenis_armada, total_baris, total_muatan
        armada_index = None
        jenis_armada = ""
        total_baris = 0
        total_muatan = 0
        ringkasan.clear()
        self.entry_armada.text = ""
        self.entry_baris.text = ""
        self.entry_muatan.text = ""
        self.refresh_text()

    def proses_item(self, *_):
        global item_ke, sisa_muatan
        try:
            nama = self.entry_item.text
            total_karton = int(self.entry_karton.text)
            isi_sebelum = int(self.entry_tambah.text or 0)
            perbaris = int(self.entry_perbaris.text)
        except:
            popup_info("Error", "Input item harus angka")
            return

        karton_terpakai = max(0, total_karton - isi_sebelum)
        baris = math.ceil(karton_terpakai / perbaris)
        baris_per_item.append(baris)

        sisa_slot = perbaris - (karton_terpakai % perbaris or perbaris)
        sisa_karton = perbaris - sisa_slot

        sisa_muatan -= total_karton
        item_ke += 1

        teks = (
            f"\nITEM {item_ke}\n"
            f"{nama} : {total_karton}\n"
            f"           +{isi_sebelum}\n"
            f"           {perbaris} × {baris - 1} = {perbaris * (baris - 1)}\n"
            f"                             {[sisa_karton]}\n"
            f"Slot akhir        : {sisa_slot}\n"
            f"Sisa muatan  : {sisa_muatan}\n"
        )

        item_list.append(teks)
        self.refresh_text()

        self.entry_item.text = ""
        self.entry_karton.text = ""
        self.entry_tambah.text = ""
        self.entry_perbaris.text = ""

    def reset_item(self, *_):
        global item_ke, sisa_muatan
        if item_list:
            item_list.pop()
            baris_per_item.pop()
            item_ke -= 1
            sisa_muatan = total_muatan
            for teks in item_list:
                for line in teks.splitlines():
                    if " : " in line and not line.startswith("ITEM"):
                        try:
                            sisa_muatan -= int(line.split(":")[1])
                        except:
                            pass
            self.refresh_text()

    def simpan_hasil(self, *_):
        popup_info("Info", "Item sudah tersimpan")

    def copy_ringkasan(self, *_):
        Clipboard.copy("".join(ringkasan + item_list))
        popup_info("Info", "Ringkasan disalin")

    def reset_semua(self, *_):
        global item_ke, sisa_muatan, armada_index
        ringkasan.clear()
        item_list.clear()
        baris_per_item.clear()
        item_ke = 0
        armada_index = None
        sisa_muatan = 0
        self.text_hasil.text = ""

class ArmadaApp(App):
    def build(self):
        return ArmadaUI()

if __name__ == "__main__":
    ArmadaApp().run()
