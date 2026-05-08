from django.shortcuts import render
from execucaoMetodos import CaixeiroViajante

def home(request):
    return render(request, 'home.html')

def algBasicos(request):
    # Valores padrão
    exec_type = 'FIXO'
    size = 8
    method = 'SE'
    tmax = 8
    ti = 100
    tf = 0.1
    fr = 0.8
    
    problem_display = ''
    initial_display = ''
    result_display = ''
    
    # Recuperar valores da sessão se existirem
    if 'exec_type' in request.session:
        exec_type = request.session['exec_type']
    if 'size' in request.session:
        size = request.session['size']
    if 'method' in request.session:
        method = request.session['method']
    if 'tmax' in request.session:
        tmax = request.session['tmax']
    if 'ti' in request.session:
        ti = request.session['ti']
    if 'tf' in request.session:
        tf = request.session['tf']
    if 'fr' in request.session:
        fr = request.session['fr']
    if 'problem_display' in request.session:
        problem_display = request.session['problem_display']
    if 'initial_display' in request.session:
        initial_display = request.session['initial_display']
    if 'result_display' in request.session:
        result_display = request.session['result_display']
    
    if request.method == 'POST':
        # Atualizar parâmetros do POST
        exec_type = request.POST.get('exec_type', 'FIXO')
        size = int(request.POST.get('size', 8))
        method = request.POST.get('method', 'SE')
        tmax = int(request.POST.get('tmax', size))
        ti = int(request.POST.get('ti', 100))
        tf = float(request.POST.get('tf', 0.1))
        fr = float(request.POST.get('fr', 0.8))
        action = request.POST.get('action', '')
        
        # Salvar na sessão
        request.session['exec_type'] = exec_type
        request.session['size'] = size
        request.session['method'] = method
        request.session['tmax'] = tmax
        request.session['ti'] = ti
        request.session['tf'] = tf
        request.session['fr'] = fr
        
        # Criar instância do algoritmo
        cv = CaixeiroViajante(tamanho=size, tipo_execucao=exec_type)
        
        if action == 'generate':
            problem_display = cv.gerar_problema()
            request.session['cv'] = {
                'distancias': cv.distancias,
                'exec_type': exec_type,
                'size': size
            }
            initial_display = ''
            result_display = ''
        
        elif action == 'initial':
            # Recuperar dados salvos
            if 'cv' in request.session:
                cv.distancias = request.session['cv']['distancias']
                cv.tipo_execucao = request.session['cv']['exec_type']
            else:
                problem_display = cv.gerar_problema()
                request.session['cv'] = {
                    'distancias': cv.distancias,
                    'exec_type': exec_type,
                    'size': size
                }
            
            initial_display = cv.solucao_inicial()
            request.session['cv']['solucao_atual'] = cv.solucao_atual
            request.session['cv']['valor_atual'] = cv.valor_atual
            request.session['cv']['melhor_solucao'] = cv.melhor_solucao
            request.session['cv']['melhor_valor'] = cv.melhor_valor
            result_display = ''
        
        elif action == 'run':
            # Recuperar dados salvos
            if 'cv' in request.session:
                cv.distancias = request.session['cv']['distancias']
                cv.solucao_atual = request.session['cv'].get('solucao_atual')
                cv.valor_atual = request.session['cv'].get('valor_atual')
                cv.melhor_solucao = request.session['cv'].get('melhor_solucao')
                cv.melhor_valor = request.session['cv'].get('melhor_valor', float('inf'))
            
            if cv.solucao_atual is None:
                result_display = "Gere a solução inicial primeiro!"
            else:
                if method == 'SE':
                    result_display = cv.subida_encosta()
                elif method == 'SET':
                    result_display = cv.subida_encosta_tentativas(tmax)
                elif method == 'TE':
                    result_display = cv.tempera_simulada(ti, tf, fr)
                elif method == 'COMP':
                    result_display = cv.analise_comparativa()
                
                # Atualizar dados na sessão
                request.session['cv']['solucao_atual'] = cv.solucao_atual
                request.session['cv']['valor_atual'] = cv.valor_atual
                request.session['cv']['melhor_solucao'] = cv.melhor_solucao
                request.session['cv']['melhor_valor'] = cv.melhor_valor
        
        # Salvar displays na sessão
        request.session['problem_display'] = problem_display
        request.session['initial_display'] = initial_display
        request.session['result_display'] = result_display
    
    context = {
        'exec_type': exec_type,
        'size': size,
        'method': method,
        'tmax': tmax,
        'ti': ti,
        'tf': tf,
        'fr': fr,
        'problem_display': problem_display,
        'initial_display': initial_display,
        'result_display': result_display,
    }
    
    return render(request, 'algBasicos.html', context)

def algGeneticos(request):
    return render(request, 'algGeneticos.html')

def sobre(request):
    return render(request, 'sobre.html')