import pickle  # запись объекта в файл
import sys
from time import perf_counter  # таймер


# КЛАСС ДЛЯ ПОСТРОЕНИЯ ДЕРЕВА
class Node:


	def __init__(self, l = None, r = None):
		self.left = l
		self.right = r

	def __str__(self):
		return f"{self.left}{self.right}"

	def codes(self, p = '', d = None):  # рекурсивно идет к каждому "листу" вычисляя путь (код) к нему
		if d is None:
			d = {}
		if type(self.left) is str:
			d.update({self.left: p + '0'})
		else:
			self.left.codes(p + '0', d)
		if type(self.right) is str:
			d.update({self.right: p + '1'})
		else:
			self.right.codes(p + '1', d)
		return d


# ------------------------ COMMAND-LINE ARGUMENTS CHECK ------------------------#
args = sys.argv[1:]

if len(args) != 3:
	sys.exit("incorrect arguments")
else:
	action = args[0]  # действие
	src = args[1]  # кодируемый файл
	destination = args[2]  # файл в который кодируем
# ------------------------ LABORATORNAYA ------------------------#
timer = perf_counter()
if action == 'encode':  # кодирование
	# счет вероятностей
	freq = {}
	f = open(src, "r")
	c = f.read(1)
	byte_count_1 = 0  # размер исходника
	while c:
		freq[c] = freq.get(c, 0) + 1
		c = f.read(1)
		byte_count_1 += 1
	f.close()

	nodes = sorted(freq.items(), key = lambda x: x[1])

	# создание дерева и вычисление кодов
	while len(nodes) > 1:
		n1 = nodes.pop(0)
		n2 = nodes.pop(0)
		node = Node(n1[0], n2[0])
		nodes.append((node, n1[1] + n2[1]))
		nodes.sort(key = lambda x: x[1])

	root = nodes[0][0]  # корневой узел дерева
	codes = root.codes()  # вычисляем коды символов

	src = open(src, "r")
	bit_text = src.read()
	src.close()
	bits = ''.join([codes[i] for i in bit_text])  # кодирование каждой буквы

	dest = open(destination, "wb")

	bit_freq = pickle.dumps(freq)  # запись словаря {буква: частота} в двоичный вид, с возможностью восстановления
	dest.write(len(bit_freq).to_bytes(4, 'big'))  # длина двоичного словаря для последующего чтения

	bits += '0' * ((8 - len(bits) % 8) % 8)  # дополняем до целого числа байтов

	buffer = bytearray()  # buffer для двоичного кода
	for i in range(0, len(bits), 8):
		buffer.append(int(bits[i:i + 8], 2))  # преобразуем в байты
	dest.write(bit_freq)
	dest.write(buffer)
	byte_count_2 = len(buffer) + len(bit_freq) + 4  # размер получившегося файла
	dest.close()
	print("ENCODED", f"{byte_count_2 / byte_count_1 * 100:.1f}%, for {perf_counter() - timer:.2f} sec")

elif action == 'decode':  # декодирование
	src = open(src, "rb")
	freq_size = int.from_bytes(src.read(4), 'big')  # читаем размер вероятностей
	freq = pickle.loads(src.read(freq_size))  # читаем вероятности
	nodes = sorted(freq.items(), key = lambda x: x[1])

	# создание дерева и вычисление кодов по сохраненным вероятностям
	while len(nodes) > 1:
		n1 = nodes.pop(0)
		n2 = nodes.pop(0)
		node = Node(n1[0], n2[0])
		nodes.append((node, n1[1] + n2[1]))
		nodes.sort(key = lambda x: x[1])

	root = nodes[0][0]  # корневой узел дерева
	codes = root.codes()  # вычисляем коды символов

	decodes = {j: i for i, j in codes.items()}  # {код: значение} -> {значение: код}
	bits = src.read()

	bit_text = ''
	for byte in bits:
		bit_text += f"{byte:08b}"  # преобразуем байты в двоичные строки 01101...

	dest = open(destination, "w")
	code = ''
	for i in bit_text:  # идем по двочному тексту, как только встречается существующий код, записываем в файл соответсвующий символ
		code += i
		if code in decodes:
			dest.write(decodes[code])
			code = ''

	dest.close()
	src.close()
	print(f"DECODED for {perf_counter() - timer:.2f} sec")
