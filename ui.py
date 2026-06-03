import ctypes
import os

from PySide6.QtCore import (
    QEvent,
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QBoxLayout,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class GlowTextEdit(QTextEdit):
    """Caixa principal com hover mais vivo, sem mudar layout."""

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(79, 70, 229, 0))
        self.setGraphicsEffect(self.glow)

        self.animation = QPropertyAnimation(self.glow, b"blurRadius", self)
        self.animation.setDuration(140)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setProperty("hovering", False)

    def enterEvent(self, event):
        self.set_hover_active(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        parent = self.parentWidget()
        still_inside_parent = bool(
            parent and parent.rect().contains(parent.mapFromGlobal(QCursor.pos()))
        )
        self.set_hover_active(still_inside_parent)
        super().leaveEvent(event)

    def set_hover_active(self, active):
        if self.property("hovering") != active:
            self.setProperty("hovering", active)
            self.style().unpolish(self)
            self.style().polish(self)

        if active:
            self.glow.setColor(QColor(79, 70, 229, 105))
            end_radius = 14
        else:
            end_radius = 0

        self.animation.stop()
        self.animation.setStartValue(self.glow.blurRadius())
        self.animation.setEndValue(end_radius)
        self.animation.start()


class GlowButton(QPushButton):
    """Botao com hover mais presente, sem foco pontilhado nem shift de layout."""

    def __init__(self, text=""):
        super().__init__(text)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoDefault(False)
        self.setDefault(False)

        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(79, 70, 229, 0))
        self.setGraphicsEffect(self.glow)

        self.animation = QPropertyAnimation(self.glow, b"blurRadius", self)
        self.animation.setDuration(130)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        color = QColor(79, 70, 229, 130)
        if self.objectName() == "Danger":
            color = QColor(220, 38, 38, 130)
        elif self.objectName() == "Ghost":
            color = QColor(82, 82, 91, 120)

        self.glow.setColor(color)
        self.animation.stop()
        self.animation.setStartValue(self.glow.blurRadius())
        self.animation.setEndValue(14)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.glow.blurRadius())
        self.animation.setEndValue(0)
        self.animation.start()
        super().leaveEvent(event)


class SettingsButton(GlowButton):
    """Icone de configuracao sem caixa de hover."""

    def enterEvent(self, event):
        self.setIconSize(QSize(23, 23))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(QSize(20, 20))
        super().leaveEvent(event)


class HistoryButton(QPushButton):
    """Seta de historico com hover sutil por crescimento."""

    def __init__(self, base_icon_size=12, hover_icon_size=15):
        super().__init__()
        self.base_icon_size = base_icon_size
        self.hover_icon_size = hover_icon_size
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoDefault(False)
        self.setDefault(False)

    def enterEvent(self, event):
        if self.isEnabled():
            self.setIconSize(QSize(self.hover_icon_size, self.hover_icon_size))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(QSize(self.base_icon_size, self.base_icon_size))
        super().leaveEvent(event)


class ResponseArea(QWidget):
    """Mantem as setas sobre a resposta sem bloquear scroll/clique do texto."""

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.nav_widget = None
        self.setMouseTracking(True)
        self.text_edit.setMouseTracking(True)
        self.installEventFilter(self)
        self.text_edit.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.text_edit)

    def set_navigation_widget(self, nav_widget):
        self.nav_widget = nav_widget
        self.nav_widget.setParent(self)
        self.nav_widget.setMouseTracking(True)
        self.nav_widget.installEventFilter(self)
        for child in self.nav_widget.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)
        self.nav_widget.raise_()
        self._position_navigation()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_navigation()

    def _position_navigation(self):
        if not self.nav_widget:
            return

        text_rect = self.text_edit.geometry()
        control_height = 24
        x = text_rect.x()
        y = max(text_rect.y(), text_rect.bottom() - control_height - 6)
        self.nav_widget.setGeometry(x, y, text_rect.width(), control_height)

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.Leave,
            QEvent.Type.MouseMove,
            QEvent.Type.HoverMove,
        ):
            self._sync_hover_state()

        return super().eventFilter(watched, event)

    def enterEvent(self, event):
        self._sync_hover_state(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._sync_hover_state()
        super().leaveEvent(event)

    def _sync_hover_state(self, force_active=None):
        active = force_active
        if active is None:
            active = self.rect().contains(self.mapFromGlobal(QCursor.pos()))

        self.text_edit.set_hover_active(active)


class DropdownPopup(QFrame):
    """Popup flutuante com cantos arredondados controlados."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("DropdownPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.content = QWidget(self)
        self.content.setObjectName("DropdownContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(4)
        self.content_height = 0
        self.hide()

    def set_content_height(self, height):
        self.content_height = height
        self._position_content()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_content()

    def _position_content(self):
        self.content.setFixedWidth(self.width())
        if self.content_height:
            self.content.setFixedHeight(self.content_height)
            y = self.height() - self.content_height
            self.content.move(0, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QPen(QColor("#4f46e5"), 1))
        painter.setBrush(QColor("#2a2f3b"))
        painter.drawRoundedRect(rect, 8, 8)
        super().paintEvent(event)


class AnimatedComboBox(QWidget):
    """Dropdown customizado com popup arredondado e seta animada."""

    currentTextChanged = Signal(str)

    def __init__(self, assets_dir):
        super().__init__()
        self.assets_dir = assets_dir
        self.items = []
        self.current_index = -1
        self.hovered = False
        self.popup_open = False
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.label = QLabel(self)
        self.label.setStyleSheet(
            "background: transparent; color: #f4f4f5; font-weight: 600;"
        )
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.popup = DropdownPopup(self)
        self.popup_layout = self.popup.content_layout
        self.popup.setStyleSheet(
            """
            QFrame#DropdownPopup {
                background-color: transparent;
                border: 0;
            }

            QPushButton#DropdownOption {
                background-color: transparent;
                border: 0;
                border-radius: 6px;
                color: #f4f4f5;
                font-weight: 600;
                min-height: 28px;
                padding: 4px 10px;
                text-align: left;
            }

            QPushButton#DropdownOption[selected="true"] {
                background-color: #353a46;
                color: #ffffff;
            }

            QPushButton#DropdownOption:hover {
                background-color: #3d4350;
                color: #ffffff;
            }
            """
        )

        self._arrow_angle = -90.0
        self.arrow_animation = QPropertyAnimation(self, b"arrowAngle", self)
        self.arrow_animation.setDuration(160)
        self.arrow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.popup_animation = QPropertyAnimation(self.popup, b"geometry", self)
        self.popup_animation.setDuration(180)
        self.popup_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.popup_animation.finished.connect(self._finish_popup_animation)
        self.popup_opacity = QGraphicsOpacityEffect(self.popup)
        self.popup.setGraphicsEffect(self.popup_opacity)
        self.popup_opacity.setOpacity(0.0)
        self.popup_fade_animation = QPropertyAnimation(
            self.popup_opacity,
            b"opacity",
            self,
        )
        self.popup_fade_animation.setDuration(140)
        self.popup_fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.popup_target_height = 0
        self.popup_closing = False

    def addItem(self, text):
        self.items.append(text)
        if self.current_index == -1:
            self.setCurrentIndex(0)

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def clear(self):
        self.items.clear()
        self.current_index = -1
        self.label.clear()
        self.hidePopup()

    def count(self):
        return len(self.items)

    def currentText(self):
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return ""

    def setCurrentIndex(self, index):
        if not 0 <= index < len(self.items):
            return

        changed = index != self.current_index
        self.current_index = index
        self.label.setText(self.items[index])
        if changed:
            self.currentTextChanged.emit(self.items[index])

    def setCurrentText(self, text):
        if text in self.items:
            self.setCurrentIndex(self.items.index(text))

    def showPopup(self):
        if self.popup.isVisible() and not self.popup_closing:
            return

        self.popup_animation.stop()
        self.popup_fade_animation.stop()
        self.popup_closing = False
        self._rebuild_popup()
        popup_parent = self.window()
        if self.popup.parentWidget() is not popup_parent:
            self.popup.setParent(popup_parent)
        self.popup.content.setFixedWidth(self.width())
        self.popup.content.adjustSize()
        self.popup_target_height = self.popup.content.sizeHint().height()
        self.popup.set_content_height(self.popup_target_height)
        popup_pos = popup_parent.mapFromGlobal(
            self.mapToGlobal(QPoint(0, self.height() + 3))
        )
        start_geometry = self._popup_geometry(0, popup_pos)
        end_geometry = self._popup_geometry(self.popup_target_height, popup_pos)
        self.popup.setGeometry(start_geometry)
        self.popup_opacity.setOpacity(0.0)
        self._set_popup_open(True)
        self.popup.show()
        self.popup.raise_()
        QApplication.instance().installEventFilter(self)
        self.popup_animation.setStartValue(start_geometry)
        self.popup_animation.setEndValue(end_geometry)
        self.popup_animation.start()
        self.popup_fade_animation.setStartValue(0.0)
        self.popup_fade_animation.setEndValue(1.0)
        self.popup_fade_animation.start()

    def hidePopup(self):
        if not self.popup.isVisible():
            self._set_popup_open(False)
            return

        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        self.popup_animation.stop()
        self.popup_fade_animation.stop()
        self.popup_closing = True
        self._set_popup_open(False)
        current_geometry = self.popup.geometry()
        end_geometry = self._popup_geometry(
            0,
            QPoint(current_geometry.x(), current_geometry.y()),
        )
        self.popup_animation.setStartValue(current_geometry)
        self.popup_animation.setEndValue(end_geometry)
        self.popup_animation.start()
        self.popup_fade_animation.setStartValue(self.popup_opacity.opacity())
        self.popup_fade_animation.setEndValue(0.25)
        self.popup_fade_animation.start()

    def enterEvent(self, event):
        self.hovered = True
        if not self.popup_open:
            self._animate_arrow(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.popup_open:
            self.hovered = False
            self._animate_arrow(False)
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.popup.isVisible():
            self.hidePopup()
        else:
            self.showPopup()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.label.setGeometry(12, 0, max(0, self.width() - 44), self.height())

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        background = QColor("#323741" if self.hovered or self.popup_open else "#2a2f3b")
        border = QColor("#4f46e5" if self.popup_open else "#4a5160" if self.hovered else "#343946")
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QPen(border, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 8, 8)

        painter.setPen(
            QPen(
                QColor("#f4f4f5"),
                2.1,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        center_x = self.width() - 18
        center_y = self.height() // 2
        painter.translate(center_x, center_y)
        painter.rotate(self._arrow_angle)
        painter.drawLine(-5, -2, 0, 3)
        painter.drawLine(0, 3, 5, -2)

    def _rebuild_popup(self):
        while self.popup_layout.count():
            item = self.popup_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for index, text in enumerate(self.items):
            option = QPushButton(text)
            option.setObjectName("DropdownOption")
            option.setProperty(
                "selected",
                "true" if index == self.current_index else "false",
            )
            option.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            option.clicked.connect(lambda checked=False, i=index: self._select_popup_item(i))
            self.popup_layout.addWidget(option)

    def _select_popup_item(self, index):
        self.setCurrentIndex(index)
        self.hidePopup()

    def _set_popup_open(self, is_open):
        self.popup_open = is_open
        if not is_open:
            self.hovered = self.underMouse()
        self._animate_arrow(is_open or self.hovered)
        self.update()

    def _finish_popup_animation(self):
        if not self.popup_closing:
            self.popup_opacity.setOpacity(1.0)
            return

        self.popup.hide()
        self.popup_closing = False
        self.popup_opacity.setOpacity(0.0)

    def eventFilter(self, watched, event):
        try:
            popup_visible = self.popup.isVisible()
        except RuntimeError:
            return False

        if popup_visible and event.type() == QEvent.Type.MouseButtonPress and hasattr(event, "globalPosition"):
            position = event.globalPosition().toPoint()
            if self.rect().contains(self.mapFromGlobal(position)):
                self.hidePopup()
                return True

            if not self.popup.rect().contains(self.popup.mapFromGlobal(position)):
                self.hidePopup()
                return False

        return super().eventFilter(watched, event)

    def _popup_geometry(self, height, position):
        return QRect(position.x(), position.y(), self.width(), height)

    def _animate_arrow(self, is_open):
        self.arrow_animation.stop()
        self.arrow_animation.setStartValue(self._arrow_angle)
        self.arrow_animation.setEndValue(0.0 if is_open else -90.0)
        self.arrow_animation.start()

    def get_arrow_angle(self):
        return self._arrow_angle

    def set_arrow_angle(self, angle):
        self._arrow_angle = angle
        self.update()

    arrowAngle = Property(float, get_arrow_angle, set_arrow_angle)


class ModernUI(QMainWindow):
    """Camada de interface, sem regras de negocio."""

    DARK_THEME = """
        QMainWindow {
            background-color: #202327;
        }

        QWidget {
            color: #e4e4e7;
            font-family: 'Segoe UI Variable', 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }

        QLabel#Label {
            color: #a1a1aa;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }

        QLabel#Hint,
        QLabel#SecurityText {
            color: #a7f3d0;
            font-size: 11px;
        }

        QLabel#StatusOk {
            color: #a7f3d0;
            font-size: 12px;
        }

        QLabel#StatusWarn {
            color: #fbbf24;
            font-size: 12px;
        }

        QWidget#ScreenRoot {
            background-color: #202327;
        }

        QFrame#Panel {
            background-color: #18181b;
            border: 1px solid #30323a;
            border-radius: 10px;
        }

        QFrame#Panel:hover {
            background-color: #1f1f23;
            border-color: #3f3f46;
        }

        QFrame#SettingsPanel {
            background-color: #24262b;
            border: 1px solid #3a3d46;
            border-radius: 10px;
        }

        QLineEdit {
            background-color: #181a1f;
            border: 1px solid #30323a;
            border-radius: 8px;
            min-height: 34px;
            padding: 6px 12px;
            color: #f4f4f5;
            font-weight: 600;
        }

        QLineEdit:hover {
            background-color: #1d2026;
            border-color: #4f46e5;
        }

        QLineEdit:focus {
            border-color: #4f46e5;
        }

        QLineEdit[state="ready"] {
            background-color: #052e23;
            border-color: #059669;
            color: #d1fae5;
        }

        QLineEdit[state="ready"]:hover,
        QLineEdit[state="ready"]:focus {
            background-color: #064e3b;
            border-color: #10b981;
        }

        QLineEdit[state="invalid"] {
            background-color: #3f1014;
            border-color: #dc2626;
            color: #fecaca;
        }

        QLineEdit[state="invalid"]:hover,
        QLineEdit[state="invalid"]:focus {
            background-color: #4c1117;
            border-color: #ef4444;
        }

        QTextEdit {
            background-color: #1c1c20;
            border: 1px solid #30323a;
            border-radius: 10px;
            padding: 14px 14px 46px 14px;
            color: #f4f4f5;
            selection-background-color: #4f46e5;
        }

        QTextEdit:hover,
        QTextEdit[hovering="true"] {
            background-color: #202126;
            border-color: #4f46e5;
        }

        QTextEdit QScrollBar:vertical {
            background: transparent;
            width: 7px;
            margin: 8px 0 48px 0;
        }

        QTextEdit QScrollBar::handle:vertical {
            background: #52525b;
            border-radius: 3px;
            min-height: 28px;
        }

        QTextEdit QScrollBar::handle:vertical:hover {
            background: #71717a;
        }

        QTextEdit QScrollBar::add-line:vertical,
        QTextEdit QScrollBar::sub-line:vertical {
            height: 0;
            background: transparent;
            border: 0;
        }

        QTextEdit QScrollBar::add-page:vertical,
        QTextEdit QScrollBar::sub-page:vertical {
            background: transparent;
        }

        QPushButton {
            background-color: #18181b;
            border: 1px solid #30323a;
            border-radius: 8px;
            color: #e4e4e7;
            font-weight: 700;
            min-height: 34px;
            outline: none;
            padding: 8px 14px;
        }

        QPushButton:focus {
            outline: none;
        }

        QPushButton:hover {
            background-color: #27272a;
            border-color: #52525b;
            color: #ffffff;
        }

        QPushButton:pressed {
            background-color: #18181b;
            border-color: #4f46e5;
        }

        QPushButton:disabled {
            background-color: #111113;
            border-color: #18181b;
            color: #52525b;
        }

        QPushButton#Primary {
            background-color: #4f46e5;
            border-color: #4f46e5;
            color: #ffffff;
        }

        QPushButton#Primary:hover {
            background-color: #4338ca;
            border-color: #4338ca;
            color: #ffffff;
        }

        QPushButton#Primary:pressed {
            background-color: #3730a3;
            border-color: #3730a3;
        }

        QPushButton#Ghost {
            background-color: transparent;
            border-color: transparent;
            color: #a1a1aa;
            padding-left: 10px;
            padding-right: 10px;
        }

        QPushButton#Ghost:hover {
            background-color: transparent;
            border-color: #52525b;
            color: #f4f4f5;
        }

        QPushButton#Danger {
            background-color: transparent;
            border-color: transparent;
            color: #a1a1aa;
        }

        QPushButton#SaveGhost {
            background-color: transparent;
            border-color: transparent;
            color: #a1a1aa;
        }

        QPushButton#SaveGhost:hover {
            background-color: transparent;
            border-color: #4f46e5;
            color: #c7d2fe;
        }

        QPushButton#SaveGhost:pressed {
            background-color: transparent;
            border-color: #3730a3;
            color: #ffffff;
        }

        QPushButton#IconButton {
            background-color: transparent;
            border-color: transparent;
            border-radius: 6px;
            color: #a1a1aa;
            min-width: 26px;
            max-width: 26px;
            min-height: 26px;
            max-height: 26px;
            padding: 2px;
        }

        QPushButton#IconButton:hover {
            background-color: transparent;
            border-color: transparent;
            color: #ffffff;
            padding: 1px;
        }

        QPushButton#IconButton:pressed {
            background-color: transparent;
            border-color: transparent;
            color: #c7d2fe;
        }

        QPushButton#HistoryButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 5px;
            min-width: 18px;
            max-width: 18px;
            min-height: 16px;
            max-height: 16px;
            padding: 0;
        }

        QPushButton#HistoryButton:hover {
            background-color: transparent;
            border-color: transparent;
        }

        QPushButton#HistoryButton:disabled {
            background-color: transparent;
            border-color: transparent;
        }

        QPushButton#Danger:hover {
            background-color: transparent;
            border-color: #dc2626;
            color: #fecaca;
        }
    """

    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(__file__)
        self.assets_dir = os.path.join(self.base_dir, "assets")

        self.setWindowTitle("PRAQ")
        self.setMinimumSize(820, 700)
        self.resize(self.minimumSize())
        self.setStyleSheet(self.DARK_THEME)
        self._apply_window_icon()
        self._apply_dark_title_bar()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_screen = self._build_main_screen()
        self.settings_screen = self._build_settings_screen()
        self.stack.addWidget(self.main_screen)
        self.stack.addWidget(self.settings_screen)

        self._apply_responsive_layout(self.width())

    def _apply_window_icon(self):
        icon_path = os.path.join(self.assets_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _apply_dark_title_bar(self):
        if os.name != "nt":
            return

        try:
            hwnd = int(self.winId())
            enabled = ctypes.c_int(1)
            caption_color = ctypes.c_int(0x00272320)
            text_color = ctypes.c_int(0x00F4F4F5)
            attributes = (
                (20, ctypes.byref(enabled), ctypes.sizeof(enabled)),
                (19, ctypes.byref(enabled), ctypes.sizeof(enabled)),
                (35, ctypes.byref(caption_color), ctypes.sizeof(caption_color)),
                (36, ctypes.byref(text_color), ctypes.sizeof(text_color)),
            )
            for attribute, value, size in attributes:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    value,
                    size,
                )
        except Exception:
            pass

    def _prepare_button(self, button):
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setAutoDefault(False)
        button.setDefault(False)
        return button

    def _create_root(self):
        root = QWidget()
        root.setObjectName("ScreenRoot")
        root.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        outer_layout = QVBoxLayout(root)
        outer_layout.setContentsMargins(56, 38, 56, 30)
        outer_layout.setSpacing(0)

        content = QWidget()
        content.setMaximumWidth(1480)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        content_row = QWidget()
        content_row_layout = QHBoxLayout(content_row)
        content_row_layout.setContentsMargins(0, 0, 0, 0)
        content_row_layout.setSpacing(0)
        content_row_layout.addStretch(1)
        content_row_layout.addWidget(content, 20)
        content_row_layout.addStretch(1)

        outer_layout.addWidget(content_row, 1)
        return root, content_layout

    def _build_main_screen(self):
        root, content_layout = self._create_root()

        header = QWidget()
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        self.logo_label = QLabel()
        logo_path = os.path.join(self.assets_dir, "logo-sem-fundo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(
                pixmap.scaledToHeight(
                    48,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("PRAQ")
            self.logo_label.setStyleSheet("font-size: 30px; font-weight: 800;")
        self.logo_label.setMinimumWidth(190)
        header_layout.addWidget(self.logo_label, 1, Qt.AlignmentFlag.AlignLeft)

        self.btn_settings = SettingsButton()
        self.btn_settings.setObjectName("IconButton")
        self.btn_settings.setToolTip("Abrir configurações")
        settings_icon = os.path.join(self.assets_dir, "settings.svg")
        if os.path.exists(settings_icon):
            self.btn_settings.setIcon(QIcon(settings_icon))
            self.btn_settings.setIconSize(QSize(20, 20))
        header_layout.addSpacing(24)
        header_layout.addWidget(self.btn_settings)

        content_layout.addWidget(header)

        selectors = QWidget()
        selectors.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.selectors_layout = QHBoxLayout(selectors)
        self.selectors_layout.setContentsMargins(0, 0, 0, 0)
        self.selectors_layout.setSpacing(10)

        self.combo_api = AnimatedComboBox(self.assets_dir)
        self.combo_api.addItems(["Gemini", "Groq"])
        self.combo_api.setToolTip("Selecionar API")
        self.combo_api.setMinimumWidth(128)
        self.combo_api.setMinimumHeight(48)
        self.combo_api.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_api.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.combo_modelos = AnimatedComboBox(self.assets_dir)
        self.combo_modelos.setToolTip("Selecionar modelo")
        self.combo_modelos.setMinimumWidth(210)
        self.combo_modelos.setMinimumHeight(48)
        self.combo_modelos.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_modelos.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.selectors_layout.addWidget(self.combo_api, 1)
        self.selectors_layout.addWidget(self.combo_modelos, 2)
        content_layout.addWidget(selectors)

        self.text_resposta = GlowTextEdit()
        self.text_resposta.setReadOnly(True)
        self.text_resposta.setPlaceholderText("A resposta da analise aparecera aqui.")
        self.text_resposta.setFont(QFont("Consolas", 11))
        self.text_resposta.setMinimumHeight(380)
        self.text_resposta.setMaximumHeight(640)
        self.text_resposta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        response_area = ResponseArea(self.text_resposta)
        response_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.history_nav_widget = QWidget()
        self.history_nav_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        history_nav_layout = QHBoxLayout(self.history_nav_widget)
        history_nav_layout.setContentsMargins(8, 0, 8, 0)
        history_nav_layout.setSpacing(2)

        self.btn_history_delete = HistoryButton(base_icon_size=13, hover_icon_size=16)
        self.btn_history_delete.setObjectName("HistoryButton")
        self.btn_history_delete.setToolTip("Excluir resposta atual")
        self.btn_history_delete.setFixedSize(20, 18)
        delete_icon = os.path.join(self.assets_dir, "x.svg")
        if os.path.exists(delete_icon):
            self.btn_history_delete.setIcon(QIcon(delete_icon))
            self.btn_history_delete.setIconSize(QSize(13, 13))

        history_nav_layout.addWidget(
            self.btn_history_delete,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        history_nav_layout.addStretch(1)

        self.btn_history_prev = HistoryButton()
        self.btn_history_prev.setObjectName("HistoryButton")
        self.btn_history_prev.setToolTip("Resposta anterior")
        self.btn_history_prev.setFixedSize(20, 18)
        prev_icon = os.path.join(self.assets_dir, "chevron-left.svg")
        if os.path.exists(prev_icon):
            self.btn_history_prev.setIcon(QIcon(prev_icon))
            self.btn_history_prev.setIconSize(QSize(12, 12))

        self.btn_history_next = HistoryButton()
        self.btn_history_next.setObjectName("HistoryButton")
        self.btn_history_next.setToolTip("Próxima resposta")
        self.btn_history_next.setFixedSize(20, 18)
        next_icon = os.path.join(self.assets_dir, "chevron-right.svg")
        if os.path.exists(next_icon):
            self.btn_history_next.setIcon(QIcon(next_icon))
            self.btn_history_next.setIconSize(QSize(12, 12))

        history_nav_layout.addWidget(
            self.btn_history_prev,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        history_nav_layout.addWidget(
            self.btn_history_next,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        response_area.set_navigation_widget(self.history_nav_widget)
        content_layout.addWidget(response_area, 1)

        self.actions_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.actions_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(10)
        self.buttons_layout.addStretch(1)

        self.btn_texto = GlowButton("Analisar F2")
        self.btn_texto.setObjectName("Primary")
        self.btn_print_unico = GlowButton("Print F8")
        self.btn_print_scroll = GlowButton("Print + Scroll F9")

        for button in (self.btn_texto, self.btn_print_unico, self.btn_print_scroll):
            button.setMinimumWidth(118)
            button.setMaximumWidth(220)

        self.buttons_layout.addWidget(self.btn_texto)
        self.buttons_layout.addWidget(self.btn_print_unico)
        self.buttons_layout.addWidget(self.btn_print_scroll)
        self.buttons_layout.addStretch(1)
        content_layout.addWidget(self.actions_widget)

        self.label_instrucoes = QLabel()
        self.label_instrucoes.setObjectName("Hint")
        self.label_instrucoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_instrucoes.setWordWrap(True)
        content_layout.addWidget(self.label_instrucoes)

        return root

    def _build_settings_screen(self):
        root, content_layout = self._create_root()
        content_layout.addSpacing(54)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        header_layout.addStretch(1)
        title = QLabel("Configurações")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f4f4f5;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, 2)
        header_layout.addStretch(1)

        content_layout.addWidget(header)
        content_layout.addSpacing(24)

        form_panel = QFrame()
        form_panel.setObjectName("SettingsPanel")
        form_panel.setFixedWidth(560)
        form_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        gemini_label = QLabel("Gemini API Key")
        gemini_label.setObjectName("Label")
        self.input_gemini_key = QLineEdit()
        self.input_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_gemini_key.setPlaceholderText("Cole a chave Gemini")
        self.input_gemini_key.setMinimumHeight(44)
        self.input_gemini_key.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        groq_label = QLabel("Groq API Key")
        groq_label.setObjectName("Label")
        self.input_groq_key = QLineEdit()
        self.input_groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_groq_key.setPlaceholderText("Cole a chave Groq")
        self.input_groq_key.setMinimumHeight(44)
        self.input_groq_key.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        form_layout.addWidget(gemini_label)
        form_layout.addWidget(self.input_gemini_key)
        form_layout.addSpacing(6)
        form_layout.addWidget(groq_label)
        form_layout.addWidget(self.input_groq_key)
        content_layout.addWidget(form_panel, 0, Qt.AlignmentFlag.AlignHCenter)
        content_layout.addSpacing(48)

        self.label_settings_status = QLabel()
        self.label_settings_status.setObjectName("StatusWarn")
        self.label_settings_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_settings_status.setWordWrap(True)
        self.label_settings_status.setMinimumHeight(22)
        content_layout.addWidget(self.label_settings_status)
        content_layout.addSpacing(26)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        actions_layout.addStretch(1)

        self.btn_back_main = GlowButton("Voltar")
        self.btn_back_main.setObjectName("Ghost")
        self.btn_back_main.setMaximumWidth(92)
        self.btn_clear_settings = GlowButton("Limpar")
        self.btn_clear_settings.setObjectName("Danger")
        self.btn_save_settings = GlowButton("Salvar")
        self.btn_save_settings.setObjectName("SaveGhost")

        actions_layout.addWidget(self.btn_back_main)
        actions_layout.addWidget(self.btn_clear_settings)
        actions_layout.addWidget(self.btn_save_settings)
        actions_layout.addStretch(1)
        content_layout.addWidget(actions)
        content_layout.addStretch(1)

        self.label_settings_footer = QLabel(
            "As chaves são armazenadas localmente com proteção do usuário do Windows."
        )
        self.label_settings_footer.setObjectName("SecurityText")
        self.label_settings_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_settings_footer.setWordWrap(True)
        content_layout.addWidget(self.label_settings_footer)

        return root

    def show_main_screen(self):
        self.input_gemini_key.clearFocus()
        self.input_groq_key.clearFocus()
        self.main_screen.setFocus()
        self.stack.setCurrentWidget(self.main_screen)

    def set_history_navigation_state(self, can_go_prev, can_go_next, can_delete=False):
        self._set_history_button_state(
            self.btn_history_delete,
            "x-active.svg" if can_delete else "x.svg",
            can_delete,
        )
        self._set_history_button_state(
            self.btn_history_prev,
            "chevron-left-active.svg" if can_go_prev else "chevron-left.svg",
            can_go_prev,
        )
        self._set_history_button_state(
            self.btn_history_next,
            "chevron-right-active.svg" if can_go_next else "chevron-right.svg",
            can_go_next,
        )

    def _set_history_button_state(self, button, icon_filename, enabled):
        icon_path = os.path.join(self.assets_dir, icon_filename)
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            icon_size = getattr(button, "base_icon_size", 12)
            button.setIconSize(QSize(icon_size, icon_size))
        button.setEnabled(True)

    def show_settings_screen(self):
        self.stack.setCurrentWidget(self.settings_screen)
        self.input_gemini_key.clearFocus()
        self.input_groq_key.clearFocus()
        self.settings_screen.setFocus()

    def clear_settings_input_focus(self):
        self.input_gemini_key.clearFocus()
        self.input_groq_key.clearFocus()
        self.settings_screen.setFocus()

    def set_settings_status(self, text, ok=False):
        self.label_settings_status.setText(text)
        self.label_settings_status.setObjectName("StatusOk" if ok else "StatusWarn")
        self.label_settings_status.style().unpolish(self.label_settings_status)
        self.label_settings_status.style().polish(self.label_settings_status)

    def set_key_field_state(self, field, state, placeholder):
        field.clear()
        field.setPlaceholderText(placeholder)
        self.set_key_field_visual(field, state)

    def set_key_field_visual(self, field, state):
        field.setProperty("state", state)
        field.style().unpolish(field)
        field.style().polish(field)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout(event.size().width())

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_dark_title_bar()

    def _apply_responsive_layout(self, width):
        compact_mode = width < 720

        if compact_mode:
            self.selectors_layout.setDirection(QBoxLayout.TopToBottom)
            self.buttons_layout.setDirection(QBoxLayout.TopToBottom)
            for button in (
                self.btn_texto,
                self.btn_print_unico,
                self.btn_print_scroll,
            ):
                button.setMaximumWidth(9999)
        else:
            self.selectors_layout.setDirection(QBoxLayout.LeftToRight)
            self.buttons_layout.setDirection(QBoxLayout.LeftToRight)
            for button in (
                self.btn_texto,
                self.btn_print_unico,
                self.btn_print_scroll,
            ):
                button.setMaximumWidth(220)

    def set_groq_mode(self, enabled):
        """Ajusta botoes e instrucoes para modo Groq."""
        self.btn_print_unico.setVisible(not enabled)
        self.btn_print_scroll.setVisible(not enabled)

        if enabled:
            self.label_instrucoes.setText("Atalho disponivel: F2 para texto selecionado")
        else:
            self.label_instrucoes.setText(
                "Atalhos: F2 para texto, F8 para print, F9 para print com scroll"
            )
