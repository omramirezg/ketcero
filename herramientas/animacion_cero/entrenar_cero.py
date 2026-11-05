"""Entrena la LeNet-5 del cuaderno Ejercicio_Densa_vs_CNN_MNIST (misma semilla, datos, optimizador y épocas)
y guarda lo que usa la animación «El cero que aprende» en datos_cero.json y cero_datos.js.

Uso:  python entrenar_cero.py
"""
import io, json, os, subprocess, time
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets

AQUI = os.path.dirname(os.path.abspath(__file__))
MNIST_DIR = r"C:\Users\USUARIO\Desktop\Maestria\2026-02\Monitoria de Deep Learning\Propuesta_2026\Semana_02\02_Clase_viernes_30_oct\1_Densa_vs_CNN_MNIST"

# --- igual que el cuaderno (celdas 2, 10, 17, 23) ---
SEMILLA = 42
torch.manual_seed(SEMILLA)
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
EPOCAS = 5


def temperatura_gpu():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                              capture_output=True, text=True).stdout.strip() + " °C"
    except OSError:
        return "sin nvidia-smi"


def crear_lenet():
    return nn.Sequential(
        nn.Conv2d(1, 6, kernel_size=5), nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(6, 16, kernel_size=5), nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(16 * 4 * 4, 120), nn.ReLU(),
        nn.Linear(120, 84), nn.ReLU(),
        nn.Linear(84, 10))


@torch.no_grad()
def puntajes(modelo, X, lote=5_000):
    modelo.eval()
    return torch.cat([modelo(X[i:i + lote].to(DISPOSITIVO)).cpu() for i in range(0, len(X), lote)])


def evaluar(modelo, X, y):
    salida = puntajes(modelo, X)
    return F.cross_entropy(salida, y).item(), (salida.argmax(1) == y).float().mean().item()


def entrenar(crear_modelo, X, y, X_val, y_val, epocas=EPOCAS, lote=128, semilla=SEMILLA):
    torch.manual_seed(semilla)
    modelo = crear_modelo().to(DISPOSITIVO)
    optimizador = torch.optim.AdamW(modelo.parameters(), lr=1e-3, weight_decay=1e-4)
    perdida_fn = nn.CrossEntropyLoss()
    Xd, yd = X.to(DISPOSITIVO), y.to(DISPOSITIVO)
    for epoca in range(epocas):
        modelo.train()
        idx = torch.randperm(len(Xd), device=DISPOSITIVO)
        for i in range(0, len(Xd), lote):
            b = idx[i:i + lote]
            optimizador.zero_grad()
            perdida = perdida_fn(modelo(Xd[b]), yd[b])
            perdida.backward()
            optimizador.step()
        p_va, a_va = evaluar(modelo, X_val, y_val)
        print(f"  época {epoca + 1}: pérdida validación {p_va:.4f}  exactitud {a_va:.2%}")
    return modelo


def main():
    t_antes = temperatura_gpu()
    print("GPU antes:", t_antes, "|", DISPOSITIVO)
    entrenamiento = datasets.MNIST(MNIST_DIR, train=True, download=False)
    prueba = datasets.MNIST(MNIST_DIR, train=False, download=False)
    X_train_todo = (entrenamiento.data.float() / 255).unsqueeze(1)
    y_train_todo = entrenamiento.targets
    X_test, y_test = (prueba.data.float() / 255).unsqueeze(1), prueba.targets
    orden = torch.randperm(len(X_train_todo), generator=torch.Generator().manual_seed(SEMILLA))
    val, tr = orden[:5_000], orden[5_000:]

    t0 = time.time()
    cnn = entrenar(crear_lenet, X_train_todo[tr], y_train_todo[tr], X_train_todo[val], y_train_todo[val])
    segundos = time.time() - t0
    _, acc_test = evaluar(cnn, X_test, y_test)
    t_despues = temperatura_gpu()
    print(f"exactitud prueba {acc_test:.2%} en {segundos:.1f} s | GPU después: {t_despues}")
    os.makedirs(os.path.join(AQUI, "modelo"), exist_ok=True)
    torch.save(cnn.state_dict(), os.path.join(AQUI, "modelo", "lenet5_mnist.pt"))

    # elegir un «0» limpio y centrado: probabilidad alta, hueco en el centro, centro de masa cerca de (13,5; 13,5)
    prob = F.softmax(puntajes(cnn, X_test), 1)
    filas = torch.arange(28).float()
    mejor, nota_mejor = None, -1e9
    for k in torch.nonzero(y_test == 0).flatten().tolist():
        im = X_test[k, 0]
        masa = im.sum()
        ci = (im.sum(1) * filas).sum() / masa
        cj = (im.sum(0) * filas).sum() / masa
        hueco = im[11:17, 11:17].mean()
        nota = prob[k, 0].log().item() * 50 - abs(ci - 13.5) - abs(cj - 13.5) - 8 * hueco.item() - abs(masa.item() - 130) / 40
        if nota > nota_mejor:
            mejor, nota_mejor = k, nota

    x = X_test[mejor:mejor + 1].to(DISPOSITIVO)
    with torch.no_grad():
        mapas = cnn[0](x)[0].cpu()                       # conv1 antes de ReLU: (6, 24, 24)
        p = F.softmax(cnn(x), 1)[0].cpu()
    pesos = cnn[0].weight.detach().cpu()[:, 0]          # (6, 5, 5)
    sesgos = cnn[0].bias.detach().cpu()

    # filtro principal: el mapa con más contraste por signo (mucho positivo y mucho negativo a la vez)
    def contraste(m):
        return min(m.clamp(min=0).sum().item(), (-m).clamp(min=0).sum().item())
    filtro = max(range(6), key=lambda f: contraste(mapas[f]))

    r = lambda t: [[round(v, 3) for v in fila] for fila in t.tolist()]
    datos = {
        "indice_prueba": mejor, "etiqueta": 0, "filtro_principal": filtro,
        "entrada": r(X_test[mejor, 0]),
        "filtros": [r(pesos[f]) for f in range(6)],
        "sesgos": [round(v, 3) for v in sesgos.tolist()],
        "mapas": [r(mapas[f]) for f in range(6)],
        "probabilidades": [round(v, 4) for v in p.tolist()],
        "exactitud_prueba": round(acc_test, 4),
        "gpu": {"antes": t_antes, "despues": t_despues, "segundos": round(segundos, 1)},
    }
    io.open(os.path.join(AQUI, "datos_cero.json"), "w", encoding="utf-8").write(json.dumps(datos, ensure_ascii=False))
    io.open(os.path.join(AQUI, "cero_datos.js"), "w", encoding="utf-8").write(
        "window.DATOS_CERO = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"0 elegido: prueba #{mejor}, p(0) = {p[0]:.4f}, filtro principal {filtro + 1}")
    print("contraste por filtro:", [round(contraste(mapas[f]), 1) for f in range(6)])


if __name__ == "__main__":
    main()
