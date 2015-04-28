
if __name__ == '__main__':
	status = 'Available'

	if status not in ['Being Made', 'Ordered']:
		print True
	else:
		print False

	dataTuple = tuple(["Data", None, 1])
	print dataTuple