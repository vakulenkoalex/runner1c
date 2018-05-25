﻿
#Область ОбработчикиСобытийФормы

Процедура ПриОткрытии()
	
	Если Не ПустаяСтрока(ПараметрЗапуска) Тогда
		ОбработатьПараметрыЗапуска(ПараметрЗапуска);
	КонецЕсли;
	
	ПодключитьОбработчикОжидания("ПроверкаВыполненостиОбновления", ИнтервалОпроса());
	
КонецПроцедуры

#КонецОбласти

#Область СлужебныеПроцедурыИФункции

Процедура ПроверкаВыполненостиОбновления()
	
	Если Не ПрочитатьСобытиеЗавершенияОбновления() Тогда
		Возврат;
	КонецЕсли;
	
	Если Не ПустаяСтрока(ОбработкаДляЗапуска) Тогда
		ОткрытьОбработку();
	КонецЕсли;
	
	ЗавершитьРаботуСистемы(Ложь);
	
КонецПроцедуры

Процедура ОбработатьПараметрыЗапуска(Знач Строка)
	ОбработкаДляЗапуска = ПрочитатьПараметрыЗапуска(Строка);
КонецПроцедуры

Процедура ОткрытьОбработку()
	
	Форма = ВнешниеОбработки.ПолучитьФорму(ОбработкаДляЗапуска);
	Форма.ОткрытьМодально();
	
КонецПроцедуры

#КонецОбласти

