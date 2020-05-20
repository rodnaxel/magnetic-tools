from openpyxl import load_workbook, Workbook

PATH_DS = '../downloads/example_dataset.xlsx'
SHEET = ''


def from_excel(path, sheet_name, rangex, rangey):
    wb = load_workbook(filename=path)
    sheet = wb[sheet_name]
    dataset = []
    for x, y in zip(sheet[rangex], sheet[rangey]):
        dataset.append((x[0].value, y[0].value))
    return dataset


def to_excel(path=None):
    # TODO: Write save dataset to .xlsx
    wb = Workbook()
    ws = wb.active
    ws['A1'] = 42
    ws.append([1,2,3])
    wb.save('./downloads/sample.xlsx')


def plot(dataset_base, dataset_finish=None, *, frame='decart'):
    """ This function used to draw  """

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    fig.set_size_inches(8.5, 8.5)

    ax.set(xlabel='B, uT', ylabel='C, uT',
           title='Magnetic ellips')

    x = [x for (x, _) in dataset_base]
    y = [y for (_, y) in dataset_base]
    ax.scatter(x, y, marker='.')

    if dataset_finish:
        xc = [x for (x, _) in dataset_finish]
        yc = [y for (_, y) in dataset_finish]
        ax.plot(xc, yc, marker='.', color='red')

    ax.grid()
    # fig.savefig("test.png")
    plt.show()