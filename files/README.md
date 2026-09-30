# RoboKin Studio

Aplicacion de escritorio en Python para el analisis cinematico de manipuladores
seriales. La primera pestana resuelve la cinematica directa por la convencion de
Denavit-Hartenberg; las demas estan preparadas como modulos vacios.

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

En Debian o Ubuntu hace falta ademas `sudo apt install python3-tk`, porque
tkinter no se distribuye por pip.

## Como esta organizado

La regla de oro del proyecto es que **el nucleo de calculo no sabe que existe
una interfaz**. Todo lo que hay en `core/` se puede importar desde un script,
una prueba automatizada o un servicio web sin arrastrar CustomTkinter.

```
robokin/
├── main.py                 Punto de entrada
├── requirements.txt
├── config/
│   └── settings.py         Paleta, radios, tipografia, limites y pestanas
├── core/                   Calculo puro (numpy + sympy), sin GUI
│   ├── robot.py            JointType, DHParameters, Joint, RobotModel
│   ├── dh.py               Matriz DH numerica y simbolica, RPY
│   ├── kinematics.py       ForwardKinematicsSolver, ForwardKinematicsResult
│   ├── presets.py          Robots de ejemplo
│   └── warmup.py           Precarga de SymPy al arrancar
├── gui/
│   ├── theme.py            Colores y fuentes cacheadas
│   ├── sidebar.py          Navegacion lateral
│   ├── app.py              Ventana principal y registro de vistas
│   ├── components/
│   │   ├── cards.py        Card, Badge, KeyValue, Divider
│   │   ├── dh_table.py     Tabla DH dinamica
│   │   └── matrix_view.py  MatrixGrid, MatrixBlock, ResultsPanel
│   └── views/
│       ├── base_view.py    BaseView y PlaceholderView
│       ├── forward_kinematics_view.py
│       ├── inverse_kinematics_view.py     (vacia)
│       ├── trajectory_view.py             (vacia)
│       └── digital_twin_view.py           (vacia)
└── utils/
    └── formatting.py       Formato de numeros, matrices y expresiones
```

## Convencion usada

Denavit-Hartenberg estandar (no la variante modificada de Craig):

```
A_i = Rot_z(theta_i) * Trans_z(d_i) * Trans_x(a_i) * Rot_x(alpha_i)

     [ c(th)  -s(th)c(al)   s(th)s(al)   a*c(th) ]
     [ s(th)   c(th)c(al)  -c(th)s(al)   a*s(th) ]
     [   0       s(al)        c(al)         d    ]
     [   0         0            0           1    ]
```

En la tabla, `a_i` es la longitud del eslabon. La variable articular se bloquea
sola segun el tipo: en una revoluta `theta_i = q_i` y en una prismatica
`d_i = q_i`. La celda bloqueada muestra el simbolo `q_i` en gris y el valor
numerico se captura en la ultima columna.

## Usar el nucleo sin interfaz

```python
from core.kinematics import solve_forward_kinematics
from core.robot import DHParameters, Joint, JointType, RobotModel

robot = RobotModel(name="Planar 2R", joints=[
    Joint(1, JointType.REVOLUTE, DHParameters(a=1.0), q=30.0),
    Joint(2, JointType.REVOLUTE, DHParameters(a=0.8), q=45.0),
])

r = solve_forward_kinematics(robot, symbolic_lengths=True, simplify=True)
print(r.position)               # [1.073081 1.272741 0.      ]
print(r.symbolic_total[0, 3])   # a1*cos(q1) + a2*cos(q1 + q2)
```

`ForwardKinematicsResult` trae las matrices `A_i` y `T_0^i` en version numerica
y simbolica, la matriz final, la posicion, los angulos RPY y los origenes de
cada sistema coordenado (listos para graficar el robot en el gemelo digital).

## Agregar una pestana nueva

1. Crear la vista en `gui/views/`, heredando de `BaseView` e implementando
   `build_body(self, parent)`.
2. Registrarla en `VIEW_REGISTRY` dentro de `gui/app.py`.
3. Agregar su clave a `NAV_ITEMS` en `config/settings.py`.

Las vistas se construyen la primera vez que se abren y luego quedan en cache,
asi que los datos capturados no se pierden al navegar entre pestanas.

## Dos restricciones de Tkinter que conviene conocer

Van a reaparecer al implementar la animacion del gemelo digital:

1. **Nunca tocar widgets desde un hilo secundario.** Ni siquiera `widget.after()`
   es seguro: lanza `RuntimeError: main thread is not in main loop`. El patron
   correcto es el que usa `forward_kinematics_view.py`: el hilo deposita el
   resultado en una `queue.Queue` y el hilo principal la consulta con
   `after(POLL_MS, ...)`.

2. **El recolector de basura puede bloquear la aplicacion.** Si el recolector
   corre dentro del hilo de calculo y libera un objeto de Tkinter (por ejemplo
   la fuente de una fila borrada de la tabla), su finalizador llama a Tcl desde
   un hilo que no es el principal y la aplicacion se congela sin error. Por eso
   el proyecto hace tres cosas: precarga SymPy en el hilo principal al arrancar
   (`core/warmup.py`), pasa fuentes cacheadas del tema al construir cada widget
   para que CustomTkinter no genere objetos de fuente huerfanos, y desactiva el
   recolector mientras dura el calculo, reactivandolo en `_finish()`.

## Verificacion

El nucleo fue contrastado contra resultados analiticos conocidos:

| Caso | Comprobacion |
|------|--------------|
| Planar 2R | La posicion coincide con `a1*cos(q1) + a2*cos(q1+q2)` hasta 1e-9 |
| Planar 2R simbolico | Con `simplify=True`, SymPy devuelve esa misma expresion |
| SCARA (RRP) | La rotacion es ortonormal y su determinante vale 1 |
| 10 GDL | Se resuelve en unos 240 ms |

## Siguientes pasos por modulo

**Cinematica inversa.** Solucion geometrica para 2 y 3 GDL, metodo numerico con
la jacobiana, multiples configuraciones (codo arriba/abajo) y verificacion de
alcanzabilidad.

**Planeacion de trayectoria.** Interpolacion polinomial de 3er y 5to orden,
perfil trapezoidal de velocidad, trayectorias cartesianas y graficas de
posicion, velocidad y aceleracion.

**Gemelo digital.** Render 3D a partir de `result.origins`, animacion de
trayectorias, espacio de trabajo alcanzable y enlace con hardware por puerto
serie o MQTT.
