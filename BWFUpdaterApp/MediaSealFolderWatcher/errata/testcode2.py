
def main():
	test = ['', 'a', 'b', 'c', 'd', '', '', '']
	pathComponents = [x for x in test if x != '']
	print pathComponents

if __name__ == '__main__':
	main()