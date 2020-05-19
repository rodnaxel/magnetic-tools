from magnetic.algorithm import Algorithm
from magnetic.util import from_excel, plot

if __name__ == '__main__':
	dataset = from_excel(
		path='./downloads/example_dataset.xlsx',
		sheet_name='Лист6',
		rangex='H7:H51',
		rangey='I7:I51'
	)
	maxdub = Algorithm(dataset)
	ds_correct = [maxdub.correct(x, y) for (x, y) in dataset]
	print(f"\n{len(dataset)}, {dataset=}\n"
	      f"{len(ds_correct)}, {ds_correct=}")
	
	print(maxdub)
	
	plot(dataset, ds_correct)
