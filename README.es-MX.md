# Levelgas para Home Assistant

[English](README.md) · [Español (México)](README.es-MX.md)

<img src="custom_components/levelgas/brand/icon.png" alt="Ícono de tanque de la integración Levelgas" width="96">

Monitorea tus tanques de gas Levelgas en Home Assistant: nivel reportado y
suavizado, estado de la batería y fecha de la última lectura.

[![Validación](https://github.com/ChaconC/ha-levelgas/actions/workflows/validate.yaml/badge.svg)](https://github.com/ChaconC/ha-levelgas/actions/workflows/validate.yaml)
[![Última versión](https://img.shields.io/github/v/release/ChaconC/ha-levelgas)](https://github.com/ChaconC/ha-levelgas/releases/latest)
[![Home Assistant 2026.10+](https://img.shields.io/badge/Home_Assistant-2026.10%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Instalación](#instalación) · [Configuración](#configuración-inicial) · [Opciones](#opciones) ·
[Suavizado](#cómo-funciona-el-suavizado) · [Solución de problemas](#solución-de-problemas) ·
[Contribuciones](#contribuciones)

> [!NOTE]
> Esta es una integración comunitaria no oficial que consulta la API de Levelgas
> en la nube. Los cambios en esa API pueden requerir una actualización de la integración.

## Funciones

- **Cuatro sensores por tanque:** nivel reportado, nivel suavizado, batería y última lectura.
- **Tendencias más estables:** una mediana móvil reduce los picos aislados del sensor.
- **Actualizaciones configurables:** elige el intervalo de consulta, la ventana de la mediana y la zona horaria.
- **Historial persistente:** el suavizado se conserva al reiniciar o actualizar la integración; ambos sensores de nivel admiten historial y estadísticas de largo plazo en Home Assistant.
- **Recuperación de sesión:** las sesiones vencidas se renuevan automáticamente; si se rechazan las credenciales, aparece una reparación en Home Assistant.
- **Sin telemetría adicional:** las credenciales y sesiones se guardan en el almacenamiento de configuración de Home Assistant.

<img src="docs/assets/sensors.png" alt="Sensores de Home Assistant con nivel del tanque, nivel suavizado, última lectura y batería" width="428">

| Sensor | Qué muestra |
| --- | --- |
| Nivel del tanque | Porcentaje reportado directamente por Levelgas |
| Nivel del tanque suavizado | Mediana móvil de lecturas distintas, con una ventana de cinco por defecto |
| Batería | Porcentaje de batería del sensor |
| Última lectura | Fecha y hora del sensor, interpretadas con la zona horaria configurada |

## Instalación

### Requisitos

- **Home Assistant 2026.10 o posterior.**
- Una cuenta de Levelgas con correo electrónico, contraseña y al menos un tanque.

### Opción 1: HACS o Marketplace

[![Abrir Levelgas en HACS o Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ChaconC&repository=ha-levelgas&category=integration)

1. Abre el repositorio con el botón de arriba y agrégalo cuando se te indique.
2. Instala **Levelgas**.
3. Reinicia Home Assistant si se solicita.
4. Continúa con la [configuración inicial](#configuración-inicial).

<details>
<summary>Agregar el repositorio personalizado manualmente</summary>

1. Abre **HACS → ⋮ → Repositorios personalizados**, o **Ajustes → Marketplace** en Home Assistant 2026.11+.
2. Agrega `https://github.com/ChaconC/ha-levelgas` con el tipo **Integración**.
3. Instala **Levelgas** y reinicia Home Assistant si se solicita.

</details>

### Opción 2: Instalación manual

1. Descarga `levelgas.zip` de la [última versión](https://github.com/ChaconC/ha-levelgas/releases/latest).
2. Extrae su contenido en `/config/custom_components/levelgas/`.
3. Reinicia Home Assistant.
4. Continúa con la [configuración inicial](#configuración-inicial).

> [!IMPORTANT]
> `manifest.json` debe quedar directamente dentro de `/config/custom_components/levelgas/`,
> sin una carpeta adicional entre ambos.

## Configuración inicial

[![Configurar Levelgas en Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=levelgas)

1. Usa el botón de arriba o abre **Ajustes → Dispositivos y servicios → Añadir integración → Levelgas**.
2. Ingresa tu correo electrónico y contraseña de Levelgas.
3. Selecciona un tanque si tu cuenta tiene varios. Si solo tiene uno, se selecciona automáticamente.
4. Repite la configuración para agregar otro tanque.

La configuración se realiza desde la interfaz de Home Assistant; no necesitas YAML.

## Opciones

Abre las opciones de la integración en **Ajustes → Dispositivos y servicios**.

| Opción | Valor predeterminado | Valores permitidos |
| --- | --- | --- |
| Intervalo de consulta | 2 horas | De 1 a 24 horas |
| Ventana de la mediana | 5 lecturas distintas | Números impares de 3 a 31 |
| Zona horaria del sensor | `America/Mexico_City` | Un nombre de zona horaria válido que coincida con el horario de tu tanque en la app de Levelgas |

> [!IMPORTANT]
> La API devuelve fechas y horas sin indicar la diferencia respecto a UTC. Usa
> la zona horaria que muestra la app de Levelgas para tu tanque. Al cambiarla,
> se borra el conjunto de muestras del suavizado y se carga uno nuevo desde el
> historial de la API.

## Cómo funciona el suavizado

El nivel suavizado usa una mediana móvil para reducir caídas falsas aisladas,
como `69 → 30 → 72`. El nivel reportado directamente sigue disponible para comparar.

- **El historial reciente de la API inicializa el filtro** en cuanto arranca la integración.
- **Solo cuentan las lecturas con fechas y horas distintas.** Consultar la misma lectura doce veces agrega una sola muestra.
- **Las muestras se conservan** al reiniciar o actualizar la integración.
- **Los atributos del sensor muestran el número de muestras, el inicio de la ventana y la fecha de la última lectura.**

> [!TIP]
> El suavizado también tarda en reflejar una recarga real de gas. Con una ventana
> completa de cinco lecturas, se necesitan tres lecturas del nuevo nivel para
> que este se convierta en la mediana. Consulta el nivel reportado directamente
> para verificar una recarga. El nivel suavizado no es un pronóstico de consumo.

> [!NOTE]
> El historial de la API inicializa el filtro, pero **no se incorpora como
> historial previo en Recorder de Home Assistant**. Home Assistant comienza a
> registrar estas entidades cuando instalas la integración.

### Ejemplo de tarjeta para el panel

Ajusta los identificadores de las entidades para que coincidan con los de tu tanque:

```yaml
type: history-graph
title: Nivel del tanque de gas
hours_to_show: 168
entities:
  - entity: sensor.levelgas_tank_level
    name: Reportado
  - entity: sensor.levelgas_tank_level_smoothed
    name: Suavizado
```

## Solución de problemas

| Síntoma | Comportamiento o siguiente paso |
| --- | --- |
| Los sensores no están disponibles | Las fallas de la API dejan los sensores como no disponibles. Los porcentajes inválidos o faltantes nunca se reemplazan por cero. |
| Se rechazan las credenciales | Abre **Ajustes → Sistema → Reparaciones** e inicia sesión de nuevo para reanudar las actualizaciones. Las sesiones vencidas se renuevan automáticamente una vez. |
| La última lectura parece antigua | Una consulta exitosa conserva la fecha real de la lectura. Es posible que el sensor aún no haya enviado una nueva. |
| La hora de la lectura es incorrecta | Revisa la zona horaria del sensor en las opciones de la integración. |
| El nivel suavizado tarda en cambiar después de una recarga | Es normal con un filtro de mediana. Compara el nivel reportado directamente y consulta [cómo funciona el suavizado](#cómo-funciona-el-suavizado). |

Para otros problemas, [abre un issue](https://github.com/ChaconC/ha-levelgas/issues).

## Contribuciones

Los pull requests ejecutan revisiones de lint y formato de Python, pruebas,
validación de metadatos de la integración, generación del archivo de instalación,
validación de HACS y hassfest. La instalación de dependencias también comprueba
que `uv.lock` coincida con `pyproject.toml`.

Consulta la [guía de desarrollo](CONTRIBUTING.md) para ver los comandos locales y
las verificaciones requeridas en los PR, el [historial de cambios](CHANGELOG.md)
para las notas de cada versión y la [licencia MIT](LICENSE).

## Desinstalación

1. Elimina cada entrada de Levelgas en **Ajustes → Dispositivos y servicios**. Esto también borra sus muestras de suavizado guardadas.
2. Desinstala **Levelgas** desde Marketplace o HACS.
3. Reinicia Home Assistant si se solicita.

El historial existente de Recorder sigue la política habitual de retención de Home Assistant.
