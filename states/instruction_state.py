import pygame

from states.main_menu import get_font


BG_DARK = (6, 14, 35)
BG_LIGHT = (24, 45, 84)
CARD_BG = (38, 53, 83)
CARD_BORDER = (74, 92, 130)
TITLE = (245, 247, 250)
HEAD_LEFT = (63, 213, 255)
HEAD_RIGHT = (255, 197, 58)
TEXT = (236, 242, 250)
KEY_BG = (90, 106, 129)
KEY_BORDER = (159, 174, 193)
RULE_DOT = (255, 175, 27)
TAB_BG = (46, 64, 96)
TAB_ACTIVE_BG = (74, 116, 196)
TAB_BORDER = (122, 150, 208)


def wrap_text(text, font, max_width):
	words = text.split(" ")
	lines = []
	current = ""

	for word in words:
		candidate = word if not current else f"{current} {word}"
		if font.size(candidate)[0] <= max_width:
			current = candidate
		else:
			if current:
				lines.append(current)
			current = word

	if current:
		lines.append(current)

	return lines


def draw_gradient_background(screen):
	width, height = screen.get_size()
	for x in range(width):
		t = x / max(1, width - 1)
		color = (
			int(BG_LIGHT[0] + (BG_DARK[0] - BG_LIGHT[0]) * t),
			int(BG_LIGHT[1] + (BG_DARK[1] - BG_LIGHT[1]) * t),
			int(BG_LIGHT[2] + (BG_DARK[2] - BG_LIGHT[2]) * t),
		)
		pygame.draw.line(screen, color, (x, 0), (x, height))


def draw_key_row(screen, labels, x, y, box_w, box_h, gap, key_font):
	for index, label in enumerate(labels):
		rect = pygame.Rect(x + index * (box_w + gap), y, box_w, box_h)
		pygame.draw.rect(screen, KEY_BG, rect, border_radius=12)
		pygame.draw.rect(screen, KEY_BORDER, rect, width=2, border_radius=12)
		render = key_font.render(label, True, TITLE)
		screen.blit(render, render.get_rect(center=rect.center))


def draw_rules(screen, rules, body_font, x, y, max_width, max_height, number_radius=14):
	line_height = body_font.get_linesize() + 6
	y_cursor = y

	for index, rule in enumerate(rules, start=1):
		if y_cursor + number_radius * 2 > y + max_height:
			break

		circle = (x + number_radius, y_cursor + number_radius)
		pygame.draw.circle(screen, RULE_DOT, circle, number_radius)
		num = body_font.render(str(index), True, (255, 255, 255))
		screen.blit(num, num.get_rect(center=circle))

		text_x = x + number_radius * 2 + 12
		for line in wrap_text(rule, body_font, max_width - (number_radius * 2 + 12)):
			if y_cursor + line_height > y + max_height:
				return
			text = body_font.render(line, True, TEXT)
			screen.blit(text, (text_x, y_cursor))
			y_cursor += line_height

		y_cursor += 8


def run(screen, clock, _payload=None):
	width, height = screen.get_size()
	title_font = get_font(max(44, int(height * 0.07)), bold=True)
	section_font = get_font(max(22, int(height * 0.036)), bold=True)
	body_font = get_font(max(16, int(height * 0.026)), bold=False)
	hint_font = get_font(max(14, int(height * 0.02)), bold=False)
	tab_font = get_font(max(16, int(height * 0.024)), bold=True)

	outer = pygame.Rect(24, 16, width - 48, height - 32)
	left_box = pygame.Rect(outer.left + 32, outer.top + 132, outer.width // 2 - 46, outer.height - 172)
	right_box = pygame.Rect(outer.centerx + 14, outer.top + 132, outer.width // 2 - 46, outer.height - 172)

	tab_width = 150
	tab_height = 40
	tab_gap = 12
	tabs_total = tab_width * 2 + tab_gap
	tab_start_x = width // 2 - tabs_total // 2
	tab_y = outer.top + 88
	pve_tab_rect = pygame.Rect(tab_start_x, tab_y, tab_width, tab_height)
	pvp_tab_rect = pygame.Rect(tab_start_x + tab_width + tab_gap, tab_y, tab_width, tab_height)

	mode = "pve"

	pve_rules = [
		"Bạn điều khiển 1 nhân vật bằng WASD để né đội AI truy đuổi",
		"Ăn chấm vàng để tăng Mục tiêu",
		"Ăn đủ Mục tiêu sẽ thắng ngay (Dễ 3, Trung bình 3, Khó 4)",
		"Ăn ô xanh để tăng tốc 4.2 giây (có thể cộng dồn)",
		"Nếu AI chạm vào người chơi thì thua",
		"Nếu sống đến hết thời gian thì thắng",
	]

	pvp_rules = [
		"Player 1 dùng WASD, Player 2 dùng phím mũi tên để di chuyển",
		"Ký hiệu: [D] là người đuổi, [C] là người chạy",
		"Ban đầu Player 2 là người đuổi",
		"Người đuổi chạm đối thủ sẽ đổi vai cho người còn lại",
		"Sau mỗi lần đổi vai có hồi 0.8 giây để tránh chạm liên hoàn",
		"HUD luôn hiển thị rõ [D]/[C] theo vai hiện tại",
		"Trận đấu kéo dài 60 giây",
		"Khi hết giờ, ai còn là người đuổi sẽ thua",
	]

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return "quit", None
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return "menu", None
				if event.key in (pygame.K_1, pygame.K_KP1):
					mode = "pve"
				if event.key in (pygame.K_2, pygame.K_KP2):
					mode = "pvp"
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if pve_tab_rect.collidepoint(event.pos):
					mode = "pve"
				if pvp_tab_rect.collidepoint(event.pos):
					mode = "pvp"

		draw_gradient_background(screen)

		title = title_font.render("Hướng Dẫn Chơi", True, TITLE)
		screen.blit(title, title.get_rect(center=(width // 2, outer.top + 54)))

		for rect, label, key in ((pve_tab_rect, "PvE", "pve"), (pvp_tab_rect, "PvP", "pvp")):
			active = mode == key
			pygame.draw.rect(screen, TAB_ACTIVE_BG if active else TAB_BG, rect, border_radius=10)
			pygame.draw.rect(screen, TAB_BORDER, rect, width=2, border_radius=10)
			label_surface = tab_font.render(label, True, TITLE)
			screen.blit(label_surface, label_surface.get_rect(center=rect.center))

		pygame.draw.rect(screen, CARD_BG, left_box, border_radius=20)
		pygame.draw.rect(screen, CARD_BG, right_box, border_radius=20)
		pygame.draw.rect(screen, CARD_BORDER, left_box, width=2, border_radius=20)
		pygame.draw.rect(screen, CARD_BORDER, right_box, width=2, border_radius=20)

		left_head = section_font.render("Điều Khiển", True, HEAD_LEFT)
		right_head = section_font.render("Luật Chơi", True, HEAD_RIGHT)
		screen.blit(left_head, (left_box.left + 24, left_box.top + 20))
		screen.blit(right_head, (right_box.left + 24, right_box.top + 20))

		content_x = left_box.left + 24
		content_width = left_box.width - 48
		key_gap = 12
		key_size = min(72, max(56, (content_width - key_gap * 3) // 4))
		key_font = get_font(max(30, int(key_size * 0.6)), bold=True)

		if mode == "pve":
			p1 = body_font.render("Người chơi (PvE): Di chuyển", True, TEXT)
			screen.blit(p1, (content_x, left_box.top + 95))
			draw_key_row(screen, ["W", "A", "S", "D"], content_x, left_box.top + 145, key_size, key_size, key_gap, key_font)

			esc_hint = body_font.render("ESC: Tạm dừng / mở menu pause", True, TEXT)
			screen.blit(esc_hint, (content_x, left_box.top + 255))

			obj_hint = body_font.render("Chấm vàng: +1 Mục tiêu", True, TEXT)
			screen.blit(obj_hint, (content_x, left_box.top + 305))

			boost_hint = body_font.render("Ô xanh: Buff tăng tốc 4.2s", True, TEXT)
			screen.blit(boost_hint, (content_x, left_box.top + 350))
			rules = pve_rules
		else:
			p1 = body_font.render("Player 1: Di chuyển", True, TEXT)
			screen.blit(p1, (content_x, left_box.top + 95))
			draw_key_row(screen, ["W", "A", "S", "D"], content_x, left_box.top + 145, key_size, key_size, key_gap, key_font)

			p2 = body_font.render("Player 2: Di chuyển", True, TEXT)
			screen.blit(p2, (content_x, left_box.top + 255))
			draw_key_row(screen, ["↑", "←", "↓", "→"], content_x, left_box.top + 305, key_size, key_size, key_gap, key_font)
			rules = pvp_rules

		draw_rules(
			screen,
			rules,
			body_font,
			right_box.left + 24,
			right_box.top + 95,
			right_box.width - 48,
			right_box.height - 120,
			number_radius=14,
		)

		hint = hint_font.render("Nhấn 1: PvE | 2: PvP | ESC để quay lại", True, (185, 199, 222))
		screen.blit(hint, hint.get_rect(center=(width // 2, height - 18)))

		pygame.display.flip()
		clock.tick(60)
