from django.shortcuts import render
from execucaoMetodos import CaixeiroViajante

def home(request):
    return render(request, 'home.html')

def algBasicos(request):
    # Helpers de conversão
    def parse_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def parse_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

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
        size = parse_int(request.POST.get('size', size), size)
        method = request.POST.get('method', 'SE')
        tmax = parse_int(request.POST.get('tmax', tmax), tmax)
        ti = parse_int(request.POST.get('ti', ti), ti)
        tf = parse_float(request.POST.get('tf', tf), tf)
        fr = parse_float(request.POST.get('fr', fr), fr)
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
    def parse_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def parse_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    exec_type = 'FIXO'
    size = 8
    selection = 'ROULETTE'
    pop_size = 40
    generations = 100
    crossover_rate = 0.9
    mutation_rate = 0.1
    tournament_size = 3
    elitism = 1

    problem_display = ''
    result_display = ''

    if 'exec_type_ga' in request.session:
        exec_type = request.session['exec_type_ga']
    if 'size_ga' in request.session:
        size = request.session['size_ga']
    if 'selection' in request.session:
        selection = request.session['selection']
    if 'pop_size' in request.session:
        pop_size = request.session['pop_size']
    if 'generations' in request.session:
        generations = request.session['generations']
    if 'crossover_rate' in request.session:
        crossover_rate = request.session['crossover_rate']
    if 'mutation_rate' in request.session:
        mutation_rate = request.session['mutation_rate']
    if 'tournament_size' in request.session:
        tournament_size = request.session['tournament_size']
    if 'elitism' in request.session:
        elitism = request.session['elitism']
    if 'problem_display_ga' in request.session:
        problem_display = request.session['problem_display_ga']
    if 'result_display_ga' in request.session:
        result_display = request.session['result_display_ga']

    if request.method == 'POST':
        exec_type = request.POST.get('exec_type', exec_type)
        size = parse_int(request.POST.get('size', size), size)
        selection = request.POST.get('selection', selection)
        pop_size = parse_int(request.POST.get('pop_size', pop_size), pop_size)
        generations = parse_int(request.POST.get('generations', generations), generations)
        crossover_rate = parse_float(request.POST.get('crossover_rate', crossover_rate), crossover_rate)
        mutation_rate = parse_float(request.POST.get('mutation_rate', mutation_rate), mutation_rate)
        tournament_size = parse_int(request.POST.get('tournament_size', tournament_size), tournament_size)
        elitism = parse_int(request.POST.get('elitism', elitism), elitism)
        action = request.POST.get('action', '')

        request.session['exec_type_ga'] = exec_type
        request.session['size_ga'] = size
        request.session['selection'] = selection
        request.session['pop_size'] = pop_size
        request.session['generations'] = generations
        request.session['crossover_rate'] = crossover_rate
        request.session['mutation_rate'] = mutation_rate
        request.session['tournament_size'] = tournament_size
        request.session['elitism'] = elitism

        cv = CaixeiroViajante(tamanho=size, tipo_execucao=exec_type)

        if action == 'generate':
            problem_display = cv.gerar_problema()
            request.session['ga'] = {
                'distancias': cv.distancias,
                'exec_type': exec_type,
                'size': size
            }
            result_display = ''

        elif action == 'run':
            if 'ga' in request.session:
                cv.distancias = request.session['ga']['distancias']
                cv.tipo_execucao = request.session['ga']['exec_type']
            else:
                problem_display = cv.gerar_problema()
                request.session['ga'] = {
                    'distancias': cv.distancias,
                    'exec_type': exec_type,
                    'size': size
                }

            result_display = cv.algoritmos_geneticos(
                pop_size=pop_size,
                generations=generations,
                selection=selection,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                tournament_size=tournament_size,
                elitism=elitism
            )

        request.session['problem_display_ga'] = problem_display
        request.session['result_display_ga'] = result_display

    context = {
        'exec_type': exec_type,
        'size': size,
        'selection': selection,
        'pop_size': pop_size,
        'generations': generations,
        'crossover_rate': crossover_rate,
        'mutation_rate': mutation_rate,
        'tournament_size': tournament_size,
        'elitism': elitism,
        'problem_display': problem_display,
        'result_display': result_display,
    }

    return render(request, 'algGeneticos.html', context)

def sobre(request):
    return render(request, 'sobre.html')