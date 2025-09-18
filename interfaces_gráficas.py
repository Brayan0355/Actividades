

# -*- coding: utf-8 -*-
# Gestor de Inventario Mini - Ferretería (sin BD) - PyQt5
# Funciones: agregar, editar (doble clic), eliminar, filtrar, exportar CSV, total del inventario.
# Estética cuidada con QSS.

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

class InventarioFerreteria(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventario de Ferretería - Mini")
        self.setGeometry(280, 200, 900, 580)
        self.setWindowIcon(QIcon("img.png"))  # opcional
        self.setObjectName("card")  # para estilo tipo tarjeta

        # Estado interno (en memoria)
        self.items = []          # [{"id":..., "nombre":..., "categoria":..., "precio":..., "stock":...}]
        self.next_id = 1
        self.modo_edicion_id = None

        self._build_ui()
        self._connect()
        # Si quieres, descomenta para pre-cargar ejemplos:
        # self._seed_demo(); self.refrescar_tabla()

    # --------------------- UI ---------------------
    def _build_ui(self):
        self.lblTitulo = QLabel("Inventario de Ferretería")
        self.lblTitulo.setObjectName("titulo")
        self.lblTitulo.setAlignment(Qt.AlignCenter)
        self.lblTitulo.setFont(QFont("Segoe UI", 12, QFont.Medium))

        # Formulario
        self.txtNombre = QLineEdit()
        self.txtNombre.setPlaceholderText("Ej.: Martillo de uña 16 oz, Broca 1/4\", Pija 1\"")

        self.cboCategoria = QComboBox()
        self.cboCategoria.addItems([
            "Herramientas",
            "Electricidad",
            "Plomería",
            "Pinturas",
            "Construcción",
            "Seguridad",
            "Jardinería",
            "Adhesivos/Selladores",
            "Tornillería/Fijaciones",
            "Medición/Nivelación",
            "Otros"
        ])

        self.spnPrecio = QDoubleSpinBox()
        self.spnPrecio.setRange(0.00, 1_000_000.00)
        self.spnPrecio.setDecimals(2)
        self.spnPrecio.setPrefix("$ ")
        self.spnPrecio.setSingleStep(0.50)

        self.spnStock = QSpinBox()
        self.spnStock.setRange(0, 1_000_000)
        self.spnStock.setSingleStep(1)

        form = QFormLayout()
        form.addRow("Nombre:", self.txtNombre)
        form.addRow("Categoría:", self.cboCategoria)

        fila_precio_stock = QHBoxLayout()
        fila_precio_stock.addWidget(QLabel("Precio unitario:"))
        fila_precio_stock.addWidget(self.spnPrecio, 1)
        fila_precio_stock.addSpacing(12)
        fila_precio_stock.addWidget(QLabel("Stock (unidades):"))
        fila_precio_stock.addWidget(self.spnStock, 1)
        form.addRow(fila_precio_stock)

        # Botones
        self.btnAgregarActualizar = QPushButton("Agregar")
        self.btnLimpiar = QPushButton("Limpiar")
        self.btnEliminar = QPushButton("Eliminar seleccionado")
        self.btnExportar = QPushButton("Exportar CSV")

        botones = QHBoxLayout()
        botones.addWidget(self.btnAgregarActualizar)
        botones.addWidget(self.btnLimpiar)
        botones.addStretch()
        botones.addWidget(self.btnEliminar)
        botones.addWidget(self.btnExportar)

        # Filtro / búsqueda
        self.txtFiltro = QLineEdit()
        self.txtFiltro.setPlaceholderText("Buscar por nombre o categoría… (ej.: tornillo, pintura, martillo)")
        self.btnFiltrar = QPushButton("Filtrar")
        self.btnQuitarFiltro = QPushButton("Quitar filtro")

        barra_filtro = QHBoxLayout()
        barra_filtro.addWidget(self.txtFiltro, 2)
        barra_filtro.addWidget(self.btnFiltrar)
        barra_filtro.addWidget(self.btnQuitarFiltro)

        # Tabla
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Categoría", "Precio", "Stock", "Subtotal"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)

        # Total
        self.lblTotal = QLabel("Total inventario: $ 0.00")
        self.lblTotal.setObjectName("total")

        # Layout principal
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(10)
        root.addWidget(self.lblTitulo)
        root.addLayout(form)
        root.addLayout(botones)
        root.addLayout(barra_filtro)
        root.addWidget(self.tabla)
        root.addWidget(self.lblTotal, alignment=Qt.AlignRight)

    # --------------------- Conexiones ---------------------
    def _connect(self):
        self.btnAgregarActualizar.clicked.connect(self.agregar_o_actualizar)
        self.btnLimpiar.clicked.connect(self.limpiar_form)
        self.btnEliminar.clicked.connect(self.eliminar_seleccionado)
        self.btnExportar.clicked.connect(self.exportar_csv)
        self.btnFiltrar.clicked.connect(self.filtrar)
        self.btnQuitarFiltro.clicked.connect(self.quitar_filtro)
        self.tabla.cellDoubleClicked.connect(self.cargar_en_form)

    # --------------------- Lógica ---------------------
    def agregar_o_actualizar(self):
        nombre = self.txtNombre.text().strip()
        categoria = self.cboCategoria.currentText()
        precio = float(self.spnPrecio.value())
        stock = int(self.spnStock.value())

        if not nombre:
            QMessageBox.warning(self, "Falta información", "Ingresa el nombre del artículo.")
            return

        if self.modo_edicion_id is None:
            item = {"id": self.next_id, "nombre": nombre, "categoria": categoria,
                    "precio": precio, "stock": stock}
            self.items.append(item)
            self.next_id += 1
        else:
            for it in self.items:
                if it["id"] == self.modo_edicion_id:
                    it["nombre"] = nombre
                    it["categoria"] = categoria
                    it["precio"] = precio
                    it["stock"] = stock
                    break
            self.modo_edicion_id = None
            self.btnAgregarActualizar.setText("Agregar")

        self.refrescar_tabla()
        self.limpiar_form(mantener_foco=True)

    def limpiar_form(self, mantener_foco=False):
        self.txtNombre.clear()
        self.cboCategoria.setCurrentIndex(0)
        self.spnPrecio.setValue(0.00)
        self.spnStock.setValue(0)
        self.modo_edicion_id = None
        self.btnAgregarActualizar.setText("Agregar")
        if not mantener_foco:
            self.txtNombre.setFocus()

    def eliminar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Selecciona una fila", "Haz clic en un artículo de la tabla.")
            return

        id_eliminar = int(self.tabla.item(fila, 0).text())
        confirmar = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar el artículo con ID {id_eliminar}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            self.items = [it for it in self.items if it["id"] != id_eliminar]
            self.refrescar_tabla()
            self.limpiar_form()

    def cargar_en_form(self, fila, _col):
        self.modo_edicion_id = int(self.tabla.item(fila, 0).text())
        self.txtNombre.setText(self.tabla.item(fila, 1).text())
        categoria = self.tabla.item(fila, 2).text()
        idx = self.cboCategoria.findText(categoria)
        if idx != -1:
            self.cboCategoria.setCurrentIndex(idx)
        self.spnPrecio.setValue(float(self.tabla.item(fila, 3).text()))
        self.spnStock.setValue(int(self.tabla.item(fila, 4).text()))
        self.btnAgregarActualizar.setText("Actualizar")

    def refrescar_tabla(self, filtro_texto: str = ""):
        self.tabla.setRowCount(0)
        texto = filtro_texto.lower().strip()
        total = 0.0

        for it in self.items:
            if texto and (texto not in it["nombre"].lower() and texto not in it["categoria"].lower()):
                continue

            subtotal = it["precio"] * it["stock"]
            total += subtotal

            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            self.tabla.setItem(r, 0, QTableWidgetItem(str(it["id"])))
            self.tabla.setItem(r, 1, QTableWidgetItem(it["nombre"]))
            self.tabla.setItem(r, 2, QTableWidgetItem(it["categoria"]))
            self.tabla.setItem(r, 3, QTableWidgetItem(f"{it['precio']:.2f}"))
            self.tabla.setItem(r, 4, QTableWidgetItem(str(it["stock"])))
            self.tabla.setItem(r, 5, QTableWidgetItem(f"{subtotal:.2f}"))

            for c in [0, 3, 4, 5]:
                self.tabla.item(r, c).setTextAlignment(Qt.AlignCenter)

        self.lblTotal.setText(f"Total inventario: $ {total:.2f}")

    def exportar_csv(self):
        if not self.items:
            QMessageBox.information(self, "Sin datos", "No hay artículos para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar como", "inventario_ferreteria.csv", "CSV (*.csv)")
        if not ruta:
            return

        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("id,nombre,categoria,precio,stock,subtotal\n")
                for it in self.items:
                    subtotal = it["precio"] * it["stock"]
                    f.write(f"{it['id']},{it['nombre']},{it['categoria']},{it['precio']:.2f},{it['stock']},{subtotal:.2f}\n")
            QMessageBox.information(self, "Éxito", "Inventario exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))

    def filtrar(self):
        self.refrescar_tabla(self.txtFiltro.text())

    def quitar_filtro(self):
        self.txtFiltro.clear()
        self.refrescar_tabla()

    # Opcional: datos de ejemplo para arrancar
    def _seed_demo(self):
        demo = [
            ("Martillo de uña 16 oz", "Herramientas", 9.50, 12),
            ("Broca 1/4\" HSS", "Tornillería/Fijaciones", 1.25, 60),
            ("Teflón 1/2\" x 10m", "Plomería", 0.80, 40),
            ("Cinta aislante 18mm", "Electricidad", 0.90, 50),
            ("Pintura látex 1 galón blanco", "Pinturas", 16.75, 8),
            ("Nivel 24\"", "Medición/Nivelación", 7.90, 6),
        ]
        for nombre, cat, precio, stock in demo:
            self.items.append({"id": self.next_id, "nombre": nombre, "categoria": cat,
                               "precio": precio, "stock": stock})
            self.next_id += 1

# --------------------- Estilos (QSS) ---------------------
def aplicar_estilos(app):
    app.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #f7faff, stop:1 #eef2ff);
            color: #0f172a;
            font-size: 14px;
        }
        QWidget#card {
            background: rgba(255,255,255,0.88);
            border: 1px solid #e5e7eb;
            border-radius: 18px;
        }
        QLabel#titulo {
            font-size: 22px;
            font-weight: 600;
            color: #0b132b;
            background: rgba(255,255,255,0.6);
            border-radius: 10px;
            padding: 4px 10px;
        }
        QLabel#total {
            font-size: 16px;
            font-weight: 700;
            color: #2e7d32;
        }
        QLabel { font-weight: 500; color: #1e293b; }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 9px 10px;
            border: 2px solid #c7d2fe;
            border-radius: 10px;
            background: #ffffff;
            selection-background-color: #6366f1;
            selection-color: white;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #6366f1;
        }
        QPushButton {
            padding: 10px 16px;
            border-radius: 12px;
            border: 0;
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #6366f1, stop:1 #4f46e5);
            color: white;
            font-weight: 600;
            letter-spacing: .3px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #7c82ff, stop:1 #6059ff);
        }
        QTableWidget {
            background: #ffffff;
            alternate-background-color: #f8fafc;
            gridline-color: #e5e7eb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
        }
        QHeaderView::section {
            background: #eef2ff;
            padding: 6px;
            border: 0px;
            font-weight: 600;
        }
    """)

# --------------------- Main ---------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    aplicar_estilos(app)
    win = InventarioFerreteria()
    win.show()
    sys.exit(app.exec_())
