import pickle
import sys
from time import perf_counter


# ----- CONSTANTS ----- #
BIT_LIMIT = 32
HIGH = 2 ** BIT_LIMIT - 1
FIRST_QTR = (HIGH + 1) // 4
HALF = FIRST_QTR * 2
THIRD_QTR = FIRST_QTR * 3

# ----- FUNCTIONS ----- #
def create_freq(text):
	freq = {}
	for i in text:  # считаем частоты
		freq[i] = freq.get(i, 0) + 1
	freq = dict(sorted([i for i in freq.items()], key = lambda x: x[1], reverse = True))  # сортируем частоты
	intervals = [0]
	index_of_char = {}
	for char, repit in freq.items():  # разбиваем на интервалы и инедексы
		index_of_char.update({char: len(intervals)})
		intervals.append(intervals[len(intervals) - 1] + repit)

	return freq, intervals, index_of_char


def encode(text):
	freq, intervals, index_of_char = create_freq(text)
	total = intervals[-1]

	low = 0
	high = HIGH
	bits_to_write = 0
	encoded = []  # здесь будут закодированные символы

	for char in text:
		j = index_of_char[char]
		r = high - low + 1

		# изменяем интервал
		high = low + (intervals[j] * r) // total - 1
		low = low + (intervals[j - 1] * r) // total

		while True:
			if high < HALF:  # старший бит 0
				encoded.append('0')
				encoded.extend(['1'] * bits_to_write)
				bits_to_write = 0
			elif low >= HALF:  # старший бит 1
				encoded.append('1')
				encoded.extend(['0'] * bits_to_write)
				bits_to_write = 0
				low -= HALF
				high -= HALF
			elif FIRST_QTR <= low and high < THIRD_QTR:  # старшие биты разные
				bits_to_write += 1  # записываем условно
				low -= FIRST_QTR
				high -= FIRST_QTR
			else:
				break
			low += low
			high += high + 1

	# вот эта штука нужна, чтобы сузить интервал в конце
	# так как после прохода разброс может быть больше THIRD_QTR - FIRST_QTR
	bits_to_write += 1
	if low < FIRST_QTR:
		encoded.append('0')
		encoded.extend(['1'] * bits_to_write)
	else:
		encoded.append('1')
		encoded.extend(['0'] * bits_to_write)

	return ''.join(encoded), freq  # объединяем в строку


def decode(encoded, freq, size):
	intervals = [0]
	chars = []
	for char in freq:
		chars.append(char)
		intervals.append(intervals[-1] + freq[char])

	total = intervals[-1]  # длина всего интервала (сумма всех символов)

	if len(encoded) < BIT_LIMIT:  # берем первые BIT_LIMIT битов для value
		value = int(encoded + '0' * (BIT_LIMIT - len(encoded)), 2)
		encoded = ""
	else:  # если битов меньше, дополняем нулями
		value = int(encoded[:BIT_LIMIT], 2)
		encoded = encoded[BIT_LIMIT:]

	low = 0
	high = HIGH
	decoded = []  # здесь будут декодированные символы

	for i in range(size):
		r = high - low + 1
		f = ((value - low + 1) * total - 1) // r

		# ищем символ
		j = 1
		while j < len(intervals) and f >= intervals[j]: j += 1

		char = chars[j - 1]
		decoded.append(char)

		high = low + (intervals[j] * r) // total - 1  # пересчёт интервал
		low = low + (intervals[j - 1] * r) // total

		while True:  # нормализация и перенос
			if high < HALF: pass
			elif low >= HALF:
				low -= HALF
				high -= HALF
				value -= HALF
			elif low >= FIRST_QTR and high < THIRD_QTR:
				low -= FIRST_QTR
				high -= FIRST_QTR
				value -= FIRST_QTR
			else: break

			# еще нормализация
			low += low
			high += high + 1
			value += value

			if encoded:  # следующий бит
				value += int(encoded[0])
				encoded = encoded[1:]

	return ''.join(decoded)  # объединяем в строку

# ------------------------ COMMAND-LINE ARGUMENTS CHECK ------------------------#
args = sys.argv[1:]

if len(args) != 3:
	sys.exit("incorrect arguments")
else:
	action = args[0]
	source = args[1]
	destination = args[2]

# ------------------------ LABORATORNAYA ------------------------#

timer = perf_counter()
if action == "encode":
	with open(source) as source_file:  # чтение и кодирование
		text = source_file.read()
		code, freq = encode(text)
	size_1 = len(text)
	with open(destination, "wb") as destination_file:  # запись частот и длины
		destination_file.write(len(text).to_bytes(4, 'big'))
		bit_freq = pickle.dumps(freq)
		destination_file.write(len(bit_freq).to_bytes(4, 'big'))
		destination_file.write(bit_freq)

		code += '0' * ((8 - len(code) % 8) % 8)

		byte_array = bytearray()  # двоичное представление
		for i in range(0, len(code), 8):
			byte_array.append(int(code[i:i + 8], 2))

		destination_file.write(byte_array)  # запись в файл
	size_2 = len(byte_array)
	print("ENCODED", f"{size_2 / size_1 * 100:.1f}%, for {perf_counter() - timer:.2f} sec")

elif action == "decode":
	with open(source, "rb") as source_file:
		length = int.from_bytes(source_file.read(4))
		freq = pickle.loads(source_file.read(int.from_bytes(source_file.read(4))))
		code = source_file.read()
		code = ''.join(f"{byte:08b}" for byte in code)
		text = decode(code, freq, length)
	with open(destination, "w") as destination_file:
		destination_file.write(text)
	print(f"DECODED for {perf_counter() - timer:.2f} sec")
