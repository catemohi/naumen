import logging
from dataclasses import dataclass
from typing import Literal, Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import PageType, _get_columns_name, _get_date_range
from .parser_base import _forming_days_collecion, _forming_days_dict
from .parser_base import _parse_date_report


log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class Mttr:

    """Класс данных для хранения данных отчета MTTR.

        Attributes:
            day: день отсчёта.
            total_issues: всего обращений.
            average_mttr: cредний МТТР.
            average_mttr_tech_support: cредний МТТР тех.поддержки.

    """
    day: int
    total_issues: int
    average_mttr: float
    average_mttr_tech_support: float


def parse(text: str, *args, **kwargs) -> \
                             Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """
    log.debug('Запуск парсинг отчёта MTTR')
    soup = BeautifulSoup(text, "html.parser")
    first_day, last_day = _parse_date_report(
        soup, 'Дата регистр, с', 'Дата регистр, по')
    log.debug(f'Получены даты отчета с {first_day} по {last_day}')
    label = _get_columns_name(soup)
    log.debug(f'Получены названия столбцов {label}')
    data_table = soup.find('table', id='stdViewpart0.part0_TableList')
    data_table = data_table.find_all('tr')[3:]
    day_collection = _forming_days_collecion(
        data_table, label, PageType.MMTR_LEVEL_REPORT_PAGE)
    date_range = _get_date_range(first_day, last_day)
    days = _forming_days_dict(
        date_range, day_collection, PageType.MMTR_LEVEL_REPORT_PAGE)
    days = _mttr_data_completion(days, label)
    collection = _formating_mttr_data(days)
    log.debug(f'Парсинг завершился успешно. Колекция отчетов MTTR '
              f'с {first_day} по {last_day} содержит {len(collection)} элем.')
    return collection


def _formating_mttr_data(days: Mapping[int, Sequence]) \
                                 -> Sequence[Mttr]:
    collection = []
    for day, day_content in days.items():
        day_content = day_content[0]
        day = day_content['День']
        total_issues = day_content['Всего ТТ']
        average_mttr = day_content['Средн МТТР']
        average_mttr_tech_support = day_content['Средн МТТР ТП']
        mttr = Mttr(day, total_issues, average_mttr, average_mttr_tech_support)
        collection.append(mttr)

    return collection


def _mttr_data_completion(days: dict, lable: Sequence) -> \
                          Mapping[int, Sequence]:
    """Функция для дополнения данных отчёта MTTR.
        т.к Naumen отдает не все необходимые данные, необходимо их дополнить.
        Заполнить пропуски за не наступившие дни: MTTR будет 0%

    Args:
        days: словарь дней, где ключ номер дня
        lable: название категорий

    Returns:
        Mapping: дополненый словарь.
    """
    avg_mttr = '0.0'
    mttr = '0.0'
    issues_count = '0'
    for day, content in days.items():
        if len(content) == 0:
            days[day] = [
                dict(zip(lable, (str(day), issues_count, avg_mttr, mttr))),
                ]
    return days
