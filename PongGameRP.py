import time
import random
import RPi.GPIO as GPIO
import spidev
from rpi_ws281x import PixelStrip, Color
import math

# Konfiguracja pinów
LED_PIN = 18           # Pin GPIO do sterowania matrycą LED
LED_COUNT = 128        # 8x16 matryca LED (8x16 = 128 pikseli)
BUTTON_SPEED_PIN = 23  # Pin GPIO przycisku do zmiany szybkości piłki
BUTTON_BLOCK_PIN = 24  # Pin GPIO przycisku do zmniejszenia paletki
BUTTON_RESET_PIN = 25  # Pin GPIO przycisku do resetowania gry
BUZZER_PIN = 17        # Pin GPIO dla buzzera

# Konfiguracja MCP3008 do odczytu z potencjometrów
SPI_BUS = 0
SPI_DEVICE = 0
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1000000

# Ustawienie pinów GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_SPEED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_BLOCK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Układ danych matrycy
data = [
    [0, 15, 16, 31, 32, 47, 48, 63, 64, 79, 80, 95, 96, 111, 112, 127],
    [1, 14, 17, 30, 33, 46, 49, 62, 65, 78, 81, 94, 97, 110, 113, 126],
    [2, 13, 18, 29, 34, 45, 50, 61, 66, 77, 82, 93, 98, 109, 114, 125],
    [3, 12, 19, 28, 35, 44, 51, 60, 67, 76, 83, 92, 99, 108, 115, 124],
    [4, 11, 20, 27, 36, 43, 52, 59, 68, 75, 84, 91, 100, 107, 116, 123],
    [5, 10, 21, 26, 37, 42, 53, 58, 69, 74, 85, 90, 101, 106, 117, 122],
    [6, 9, 22, 25, 38, 41, 54, 57, 70, 73, 86, 89, 102, 105, 118, 121],
    [7, 8, 23, 24, 39, 40, 55, 56, 71, 72, 87, 88, 103, 104, 119, 120]
]

# Inicjalizacja matrycy LED
strip = PixelStrip(LED_COUNT, LED_PIN)
strip.begin()

# Mapa wartości potencjometru do zakresu wyświetlacza
def map_pot_to_display_range(pot_value, paddle_size):
    # Oblicz pozycję na podstawie wartości potencjometru
    pos = int(pot_value / 170)
    
    if paddle_size == 2:
        return max(0, min(pos, 6))  # Pozycja nie może przekroczyć 6, żeby paletka o szerokości 2 nie wychodziła poza matrycę
    elif paddle_size == 3:
        return max(0, min(pos, 5))  # Pozycja nie może przekroczyć 5, żeby paletka o szerokości 3 nie wychodziła poza matrycę


# Odczyt danych z MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((r[1] & 3) << 8) + r[2]
    return data

# Funkcje dla buzzera
def buzzer_on():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def buzzer_off():
    GPIO.output(BUZZER_PIN, GPIO.LOW)

# Rysowanie paletki gracza na matrycy LED (pionowo)
def draw_player(position, side, num):
    global cur_pos1, cur_pos2
    if side == 1:  # Gracz 1 (lewa strona)
        cur_pos1 = position
        for i in range(num):
            # Zapewniamy, że nie przekroczy zakresu planszy
            if 0 <= position + i < 8:
                strip.setPixelColor(data[position + i][0], Color(255, 0, 0))  # Red
    else:  # Gracz 2 (prawa strona)
        cur_pos2 = position
        for i in range(num):
            if 0 <= position + i < 8:
                strip.setPixelColor(data[position + i][15], Color(0, 0, 255))  # Blue
    strip.show()


# Rysowanie piłki
def draw_ball(x, y, speed):
    x = min(math.floor(x),15)
    y = min(math.floor(y),7)
    pixel_num = data[y][x]
    strip.setPixelColor(pixel_num, Color(0, 255, 0))  # Green ball
    strip.show()
    time.sleep(speed)

# Kontynuowanie gry po stracie punktu
def cont_game(player1_last, player2_last):
    global player1_score, player2_score, ball_x, ball_y, ball_dx, ball_dy
    if (player2_last == 1):
        ball_x = 8
        ball_y = 4
        ball_dx = -1
        ball_dy = 0
        player2_last = 0
    elif (player1_last == 1):
        ball_x = 8
        ball_y = 4
        ball_dx = 1
        ball_dy = 0
        player1_last = 0

# Czyszczenie matrycy LED
def clear_led_matrix():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

numbers2 =[
    [80, 81, 82, 83, 84, 85,86, 89, 102, 105, 106, 107, 108, 109, 110, 111, 96, 95],
    [95,96, 97, 98, 99, 100, 101, 102,105, 89],
    [80, 95, 96, 111, 110, 109, 108, 99, 92, 83, 84,85, 86,89,102,105],
    [80,95, 96, 110, 109, 99, 92, 83, 107, 106, 102,89, 86]
 ]

numbers1 = [
    [16, 31, 32, 47, 46, 45,44, 43, 42, 41, 38, 25, 22, 21,20,19,18,17],
    [31, 32, 33, 34,35,36,37,38,41,25],
    [16,31,32,47,46,45,44,35,28,19,20,21,22,25,38, 41],
    [16, 31, 32,46,45,19,28, 35, 43, 42, 38, 25, 22],
]

# Wyświetlanie wyniku
def show_score_for_3_seconds(score1, score2):
    clear_led_matrix()
    for i in range(0, len(numbers2[score2])):
        strip.setPixelColor(numbers2[score2][i], Color(0, 0, 255))  # Blue (Player 2)
    for i in range(0, len(numbers1[score1])):
        strip.setPixelColor(numbers1[score1][i], Color(255, 0, 0))  # Blue (Player 2)
    strip.show()
    time.sleep(3)
    clear_led_matrix()

winner_matrix =[16,17,18, 19, 20, 21,22,25,26,27,28,29,30,35,36,37,38,44,43,42,41,54,53,52,51,57,58,59,60,61,62,70,69,68,67,66,65,64, 78, 77, 76,75, 74,73,86,85,84, 83, 92, 91, 90, 89, 99, 100,101,102,105,106,107,108,109,110,118, 117,116,115, 114,113,112]

# Funkcja wyświetlająca wynik obu graczy na ekranie przez 3 sekundy.  
def end_game_screen(score1, score2):
    clear_led_matrix()
    if(score2 == 3):
        for i in range(0, len(winner_matrix)):
            strip.setPixelColor(winner_matrix[i], Color(0, 0, 255))  # Niebieski (Gracz 2)
    else: 
        for i in range(0, len(winner_matrix)):
            strip.setPixelColor(winner_matrix[i], Color(255, 0, 0))  # Czerwony (Gracz 1)
    strip.show()
    time.sleep(5)
    clear_led_matrix()
    

# Ustawienia początkowe gry
player1_score = 0
player2_score = 0
player2_last = 0
player1_last = 0
ball_x, ball_y = 8, 4
ball_dx, ball_dy = 1, 1

speed = 0.5
mode = 0
num1 = 3
num2 = 3
player1_blocked_time = None
player2_blocked_time = None

# Obsługa przycisku zmiany szybkości piłki
def increase_ball_speed(channel):
    global speed, mode
    mode += 1
    speed = 0.25 if mode % 2 == 1 else 0.5

# Obsługa przycisku zmniejszenia paletki (nazwa funkcji do zmiany!)
def block_player(channel):
    global num1, num2, player1_blocked_time, player2_blocked_time
    blocked_player = random.choice([1, 2])

    if blocked_player == 1:
        num1 = 2
        player1_blocked_time = time.time()
    else:
        num2 = 2
        player2_blocked_time = time.time()


# Reset gry
def reset_game():
    global player1_score, player2_score, ball_x, ball_y, ball_dx, ball_dy, num1, num2, speed, mode, player2_last, player1_last
    player1_score = 0
    player2_score = 0
    player2_last = 0
    player1_last = 0
    ball_x, ball_y = 7, 4
    ball_dx = random.choice([-1, 1])
    ball_dy = random.choice([-1, 0, 1])
    #ball_dx, ball_dy = 1, 0
    speed = 0.5
    mode = 0
    num1 = 3
    num2 = 3
    player1_blocked_time = 0
    player2_blocked_time = 0


# Obsługa przycisku resetu gry
def restart_game(channel):
    reset_game()


# Przypisanie obsługi przycisków
GPIO.add_event_detect(BUTTON_SPEED_PIN, GPIO.FALLING, callback=increase_ball_speed, bouncetime=300)
GPIO.add_event_detect(BUTTON_BLOCK_PIN, GPIO.FALLING, callback=block_player, bouncetime=300)
GPIO.add_event_detect(BUTTON_RESET_PIN, GPIO.FALLING, callback=restart_game, bouncetime=300)

# Główna pętla gry
try:
    while True:
        # Sprawdzanie czasu utrudnienia graczy
        if player1_blocked_time and (time.time() - player1_blocked_time >= 5):
            num1 = 3
            player1_blocked_time = 0
        if player2_blocked_time and (time.time() - player2_blocked_time >= 5):
            num2 = 3
            player2_blocked_time = 0

        # Odczyt potencjometrów i mapowanie
        player1_position = map_pot_to_display_range(read_adc(0), num1)  # Gracz 1
        player2_position = map_pot_to_display_range(read_adc(1), num2)  # Gracz 2

        # Aktualizacja pozycji paletek graczy
        draw_player(player1_position, 1, num1)
        draw_player(player2_position, 2, num2)

        # Aktualizacja piłki
        draw_ball(ball_x, ball_y, speed)

        # Przesunięcie piłki
        ball_x += ball_dx
        ball_y += ball_dy

        # Kolizje z krawędziami wyświetlacza (floora chyba mozna wywalic!)
        if math.floor(ball_y) <= 0 or math.floor(ball_y) >= 7:
            ball_dy *= -1

        # Kolizje z paletkami graczy
        if ball_x == 0 and ball_y in range(cur_pos1, cur_pos1 + num1):
            if ball_y == cur_pos1:
                ball_dy = -1  # Hit top of paddle
            elif ball_y == cur_pos1 + num1 - 1:
                ball_dy = 1   # Hit bottom of paddle
            else:
                ball_dy = 0   # Hit middle of paddle
            ball_dx *= -1
            ball_x = 1
            buzzer_on()
            time.sleep(0.1)
            buzzer_off()

        elif ball_x == 15 and ball_y in range(cur_pos2, cur_pos2 + num2):
            if ball_y == cur_pos2:
                ball_dy = -1  # Hit top of paddle
            elif ball_y == cur_pos2 + num2 - 1:
                ball_dy = 1   # Hit bottom of paddle
            else:
                ball_dy = 0   # Hit middle of paddle
            ball_dx *= -1
            ball_x = 14
            buzzer_on()
            time.sleep(0.1)
            buzzer_off()


        # Dodanie punktów i kontynuacja gry po zdobyciu punktów
        if ball_x < 0:
            player2_score += 1
            show_score_for_3_seconds(player1_score, player2_score)
            if(player2_score == 3):
                end_game_screen(player1_score, player2_score)
                reset_game()
            player2_last = 1
            player1_last = 0
            cont_game(player1_last, player2_last)
        elif ball_x > 15:            
            player1_score += 1
            show_score_for_3_seconds(player1_score, player2_score)
            if(player1_score == 3):
                end_game_screen(player1_score, player2_score)
                reset_game()
            player2_last = 0
            player1_last = 1
            cont_game(player1_last, player2_last)

        clear_led_matrix()
        time.sleep(0.01)

except KeyboardInterrupt:
    GPIO.cleanup()
    clear_led_matrix()  # Czyszczenie matrycy
    print("Game over!")



