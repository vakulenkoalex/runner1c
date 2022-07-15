﻿
#Область ОбработчикиСобытийФормы

&НаКлиенте
Процедура ПриОткрытии(Отказ)
	
	Если Не ПустаяСтрока(ПараметрЗапуска) Тогда
		ОбработатьПараметрыЗапуска(ПараметрЗапуска);
	КонецЕсли;
	
	ПодключитьОбработчикОжидания("ПроверкаВыполненностиОбновления", ИнтервалОпроса());
	
КонецПроцедуры

#КонецОбласти

#Область СлужебныеПроцедурыИФункции

&НаКлиенте
Процедура ПроверкаВыполненностиОбновления()
	
	Если Не ПрочитатьСобытиеЗавершенияОбновления() Тогда
		Возврат;
	КонецЕсли;
	
	Если Не ПустаяСтрока(ПутьКОбработкам) Тогда
		ОткрытьОбработку();
	КонецЕсли;
	
	ЗавершитьРаботуСистемы(Ложь);
	
КонецПроцедуры

&НаСервере
Функция ПрочитатьСобытиеЗавершенияОбновления()
	Возврат РеквизитФормыВЗначение("Объект").ПрочитатьСобытиеЗавершенияОбновления();
КонецФункции

&НаСервере
Функция ИнтервалОпроса()
	Возврат РеквизитФормыВЗначение("Объект").ИнтервалОпроса();
КонецФункции

&НаКлиенте
Процедура ОбработатьПараметрыЗапуска(Знач ПараметрЗапуска)
	ПутьКОбработкам = ПрочитатьПараметрыЗапуска(ПараметрЗапуска);
КонецПроцедуры

&НаСервере
Функция ПрочитатьПараметрыЗапуска(Знач Строка)
	Возврат РеквизитФормыВЗначение("Объект").ПрочитатьПараметрыЗапуска(Строка);
КонецФункции

&НаКлиенте
Процедура ОткрытьОбработку()
	
	Для Каждого Файл Из НайтиФайлы(ПутьКОбработкам, "*.epf", Истина) Цикл
		
		Адрес = "";
		
		ПоместитьФайл(Адрес, Файл.ПолноеИмя, , Ложь);
		Имя = ПодключитьВнешнююОбработку(Адрес);
		
		ОткрытьФорму(СтрШаблон("ВнешняяОбработка.%1.Форма.Форма", Имя));
		
	КонецЦикла;
	
КонецПроцедуры

&НаСервереБезКонтекста
Функция ПодключитьВнешнююОбработку(Знач Адрес)
	Возврат ВнешниеОбработки.Подключить(Адрес);
КонецФункции

#КонецОбласти
