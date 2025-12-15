// --- CONFIGURATION ---
const PB_URL = "https://api.mytripplanner.fr/";

// VOS URLS DE WEBHOOK
const WEBHOOK_FREE = "https://n8n.mytripplanner.fr/webhook/695e2724-613b-4430-bdc5-9b07dbe38fca"; 
const WEBHOOK_PREMIUM = "https://n8n.mytripplanner.fr/webhook/032ddc39-7ac3-4daa-98a6-5ae43dc25338";

// Initialisation PocketBase
const pb = new PocketBase(PB_URL);

// État de l'interface auth
let isSignupMode = false;

// --- 1. GESTION DU FLUX GRATUIT ---
async function handleFreeForm(e) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const originalBtnText = btn.innerHTML;
    
    // 1. Récupération des données
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.is_surprise = document.getElementById('free_surprise').checked;

    // Ajout des données de Google Places (si dispos)
    data.origin_lat = document.getElementById('free_origin_lat')?.value || '';
    data.origin_lng = document.getElementById('free_origin_lng')?.value || '';
    data.dest_lat = document.getElementById('free_dest_lat')?.value || '';
    data.dest_lng = document.getElementById('free_dest_lng')?.value || '';
    data.dest_type = document.getElementById('free_dest_type')?.value || '';

    // 2. VALIDATION INTELLIGENTE (Free)    
    // VERIFICATION ORIGINE
    const originInput = document.getElementById('free_origin');
    if (!originInput.value || originInput.dataset.valid !== "true") {
        Swal.fire('Ville inconnue', 'Veuillez sélectionner une ville de départ dans la liste déroulante.', 'warning');
        return;
    }

    if (!data.email || !data.email.trim()) {
        Swal.fire('Oups', 'L\'email est obligatoire.', 'warning');
        return;
    }

    // VERIFICATION DESTINATION
    const destInput = document.getElementById('free_destination');
    if (!data.is_surprise) {
        if (!destInput.value || destInput.dataset.valid !== "true") {
            Swal.fire('Destination inconnue', 'Veuillez sélectionner une destination dans la liste ou cocher "Surprends-moi".', 'warning');
            return;
        }
    }

    // UI: Chargement
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Envoi en cours...';

    try {
        const response = await fetch(WEBHOOK_FREE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            Swal.fire({
                title: 'Décollage imminent ! ✈️',
                html: `L'IA génère votre itinéraire sur mesure.<br><br>
                       Vous allez recevoir le résultat à <b>${data.email}</b> d'ici 5 à 15 minutes.<br>
                       <small class="text-slate-400">(Pensez à vérifier vos spams !)</small>`,
                icon: 'success',
                confirmButtonColor: '#0D9488',
                confirmButtonText: 'Parfait, je surveille ma boîte !'
            });
                
            const currentMode = document.querySelector('input[name="free_mode_type"]:checked').value;
            const currentOrigin = document.getElementById('free_origin').value;
            const currentEmail = form.querySelector('input[name="email"]').value;

            form.reset(); 

            // Restauration
            const originInput = document.getElementById('free_origin');
            if (originInput) {
                originInput.value = currentOrigin;
                originInput.dataset.valid = "true";
            }

            const emailInput = form.querySelector('input[name="email"]');
            if (emailInput) {
                emailInput.value = currentEmail;
            }

            const radioToRestore = document.querySelector(`input[name="free_mode_type"][value="${currentMode}"]`);
            if (radioToRestore) {
                radioToRestore.checked = true;
                toggleDateMode('free', currentMode);
            }

            const surpriseCheck = document.getElementById('free_surprise');
            if(surpriseCheck) surpriseCheck.checked = false;
            
            const destInput = document.getElementById('free_destination');
            if(destInput) {
                destInput.disabled = false;
                destInput.value = "";
                destInput.classList.remove('opacity-50', 'cursor-not-allowed');
                destInput.dataset.valid = "false";
            }
        } else {
            throw new Error("Erreur lors de l'envoi au webhook");
        }

    } catch (error) {
        console.error(error);
        Swal.fire({
            title: 'Erreur technique',
            text: "Le serveur ne répond pas. Veuillez réessayer.",
            icon: 'error',
            confirmButtonColor: '#ef4444'
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
    }
}

// --- 2. GESTION DU FLUX PREMIUM ---
async function handlePremiumForm(e) {
    e.preventDefault();
    
    if (!pb.authStore.isValid || !pb.authStore.model) {
        Swal.fire('Non connecté', 'Veuillez vous connecter pour accéder au service Premium.', 'warning');
        return;
    }

    const user = pb.authStore.model;
    const currentCredits = user.credits || 0;

    if (currentCredits < 1) {
        Swal.fire({
            title: 'Crédits insuffisants',
            text: "Il vous faut au moins 1 crédit pour générer un voyage Expert.",
            icon: 'warning',
            confirmButtonText: 'Recharger',
            confirmButtonColor: '#0D9488'
        });
        return;
    }

    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const originalBtnText = btn.innerHTML;
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    data.user_id = user.id;
    data.user_email = user.email;
    data.is_surprise = document.getElementById('prem_surprise').checked;

    if (!data.origin || !data.origin.trim()) {
        Swal.fire('Info manquante', 'La ville de départ est requise.', 'warning');
        return;
    }
    if (!data.budget || !data.budget.trim()) {
        Swal.fire('Budget requis', 'Pour un voyage Expert, le budget est essentiel.', 'warning');
        return;
    }

    if (!data.is_surprise && (!data.destination || !data.destination.trim())) {
        Swal.fire('Destination manquante', 'Indiquez une destination ou cochez le mode "Surprends-moi".', 'warning');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Analyse IA...';

    try {
        const response = await fetch(WEBHOOK_PREMIUM, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const newCredits = currentCredits - 1;
            document.getElementById('dash-credits').innerText = newCredits;
            pb.authStore.model.credits = newCredits; 

            hideModal('modal-new-trip');

            Swal.fire({
                title: 'Voyage Expert lancé !',
                html: `Votre demande est partie. Notre IA analyse les meilleures options.<br><b>Nouveau solde : ${newCredits} crédits.</b>`,
                icon: 'success',
                confirmButtonColor: '#0D9488'
            });
            
            form.reset();
            document.getElementById('prem_surprise').checked = false;
            document.getElementById('prem_dest').disabled = false;
            document.getElementById('prem_dest').classList.remove('opacity-50', 'cursor-not-allowed');

        } else {
            throw new Error("Erreur webhook premium");
        }

    } catch (error) {
        console.error(error);
        Swal.fire({
            title: 'Erreur technique',
            text: "Impossible de contacter le service Premium.",
            icon: 'error',
            confirmButtonColor: '#ef4444'
        });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
    }
}

// --- ROUTEUR ---
function router(viewName, mode = null) {
    document.querySelectorAll('.app-view').forEach(el => el.classList.add('hidden'));
    
    const target = document.getElementById('view-' + viewName);
    if (target) target.classList.remove('hidden');

    if (viewName === 'auth') {
        isSignupMode = (mode === 'signup');
        updateAuthUI();
        document.getElementById('auth-error').classList.add('hidden');
        document.getElementById('auth-email').value = '';
        document.getElementById('auth-password').value = '';
    }
    updateNavbar();
}

// --- NAVBAR ---
function updateNavbar() {
    const isLoggedIn = pb.authStore.isValid;
    const navPublic = document.getElementById('nav-public');
    const navPrivate = document.getElementById('nav-private');
    
    if (isLoggedIn) {
        navPublic.classList.add('hidden');
        navPrivate.classList.remove('hidden');
        if(pb.authStore.model) {
            document.getElementById('user-display-email').innerText = pb.authStore.model.email;
            const credits = pb.authStore.model.credits || 0;
            document.getElementById('dash-credits').innerText = credits;
        }
    } else {
        navPublic.classList.remove('hidden');
        navPrivate.classList.add('hidden');
    }
}

// --- AUTH ---
function toggleAuthMode() {
    isSignupMode = !isSignupMode;
    updateAuthUI();
}

function updateAuthUI() {
    const nameGroup = document.getElementById('group-name');
    const title = document.getElementById('auth-title');
    const sub = document.getElementById('auth-subtitle');
    const btn = document.getElementById('auth-btn-submit');
    const switchText = document.getElementById('auth-switch-text');
    const confirmGroup = document.getElementById('group-password-confirm');

    if (isSignupMode) {
        title.innerText = "Créer un compte";
        sub.innerText = "Rejoignez TripPlanner pour sauvegarder vos voyages.";
        btn.innerText = "S'inscrire";
        switchText.innerText = "Déjà inscrit ? Se connecter";
        confirmGroup.classList.remove('hidden');
        nameGroup.classList.remove('hidden');
    } else {
        title.innerText = "Connexion";
        sub.innerText = "Accédez à votre espace membre.";
        btn.innerText = "Se connecter";
        switchText.innerText = "Pas encore de compte ? S'inscrire";
        confirmGroup.classList.add('hidden');
        nameGroup.classList.add('hidden');
    }
}

// --- LOGIQUE D'AUTHENTIFICATION & INSCRIPTION ---
async function handleAuth(e) {
    e.preventDefault();
    
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const btn = document.getElementById('auth-btn-submit');
    
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = "Chargement...";

    try {
        if (isSignupMode) {
            const passConfirm = document.getElementById('auth-password-confirm').value;
            const firstName = document.getElementById('auth-name').value;

            if (password !== passConfirm) {
                throw new Error("Les mots de passe ne correspondent pas.");
            }
            if (password.length < 8) {
                throw new Error("Le mot de passe doit faire au moins 8 caractères.");
            }
            if (!firstName || !firstName.trim()) {
                throw new Error("Merci d'indiquer votre prénom.");
            }
            
            await pb.collection('users').create({
                email: email,
                password: password,
                passwordConfirm: passConfirm,
                name: firstName,
                credits: 0
            });

            await pb.collection('users').authWithPassword(email, password);

            Swal.fire({
                title: 'Bienvenue !',
                text: 'Votre compte a été créé avec succès.',
                icon: 'success',
                timer: 2000,
                showConfirmButton: false
            });

        } else {
            await pb.collection('users').authWithPassword(email, password);
        }

        router('dashboard');

    } catch (err) {
        console.error(err);
        let message = err.message;
        
        if (err.status === 400) {
            message = "Données invalides. Cet email est peut-être déjà utilisé.";
        }
        if (err.status === 400 && !isSignupMode) {
             message = "Email ou mot de passe incorrect.";
        }

        Swal.fire({
            title: 'Erreur',
            text: message,
            icon: 'error',
            confirmButtonColor: '#ef4444'
        });
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

function logout() {
    pb.authStore.clear();
    router('home');
}

// --- MODAL ---
function showModal(id) { document.getElementById(id).classList.remove('hidden'); }
function hideModal(id) { document.getElementById(id).classList.add('hidden'); }

// --- SURPRISE LOGIC ---
['free', 'prem'].forEach(prefix => {
    const check = document.getElementById(prefix + '_surprise');
    const destInput = document.getElementById(prefix + (prefix === 'free' ? '_destination' : '_dest'));
    
    if(check && destInput) {
        check.addEventListener('change', function() {
            if(this.checked) {
                destInput.disabled = true;
                destInput.value = "Choix de l'IA...";
                destInput.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                destInput.disabled = false;
                destInput.value = "";
                destInput.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
    }
});

// INIT
document.addEventListener('DOMContentLoaded', () => {
    if(pb.authStore.isValid) router('dashboard');
    else router('home');

    // 1. Formulaire Gratuit (Accueil)
    setupAutocomplete('free_origin', false);      
    setupAutocomplete('free_destination', true);

    // 2. Formulaire Premium (Modal)
    setupAutocomplete('prem_origin', false);
    setupAutocomplete('prem_dest', true);
});

// --- LOGIQUE BASCULE DATES / DURÉE ---
function toggleDateMode(prefix, mode) {
    console.log("Mode changé :", mode); // Pour vérifier dans la console (F12)

    // 1. Récupération des blocs (les conteneurs)
    const blocDuree = document.getElementById(prefix + '_bloc_duree');
    const blocDates = document.getElementById(prefix + '_bloc_dates');
    
    // 2. Récupération des champs (les inputs)
    const inputDuree = document.getElementById(prefix + '_input_duree');
    const inputDebut = document.getElementById(prefix + '_input_date_debut');
    const inputFin = document.getElementById(prefix + '_input_date_fin');

    // Sécurité : Si les éléments n'existent pas dans le HTML, on arrête pour éviter le bug
    if (!blocDuree || !blocDates) {
        console.error("Erreur : Les blocs HTML sont introuvables. Vérifiez les ID dans index.html");
        return;
    }

    if (mode === 'duree') {
        // --- CAS 1 : MODE DURÉE (Dates Flexibles) ---
        
        // On AFFICHE la durée et on CACHE les dates
        blocDuree.classList.remove('hidden');
        blocDates.classList.add('hidden');
        
        // Gestion des obligations (Required)
        if(inputDuree) inputDuree.removeAttribute('required'); // Durée optionnelle
        if(inputDebut) inputDebut.removeAttribute('required');
        if(inputFin) inputFin.removeAttribute('required');
        
        // Nettoyage
        if(inputDebut) inputDebut.value = '';
        if(inputFin) inputFin.value = '';

    } else {
        // --- CAS 2 : MODE DATES FIXES ---
        
        // On CACHE la durée et on AFFICHE les dates
        blocDuree.classList.add('hidden');
        
        // Important : On retire hidden ET on s'assure que flex est là pour l'alignement
        blocDates.classList.remove('hidden');
        blocDates.classList.add('flex'); 
        
        // Gestion des obligations (Required)
        if(inputDuree) inputDuree.removeAttribute('required');
        
        // Les dates deviennent OBLIGATOIRES
        if(inputDebut) inputDebut.setAttribute('required', '');
        if(inputFin) inputFin.setAttribute('required', '');
        
        // Nettoyage
        if(inputDuree) inputDuree.value = '';
    }
}

// --- SÉCURITÉ DES DATES ---
function updateEndDate(prefix) {
    const startInput = document.getElementById(prefix + '_input_date_debut');
    const endInput = document.getElementById(prefix + '_input_date_fin');

    if (!startInput || !endInput || !startInput.value) return;

    endInput.min = startInput.value;

    if (!endInput.value || endInput.value < startInput.value) {
        const dateObj = new Date(startInput.value);
        dateObj.setDate(dateObj.getDate());
        endInput.value = dateObj.toISOString().split('T')[0];
    }
}

function validateEndDate(prefix) {
    const startInput = document.getElementById(prefix + '_input_date_debut');
    const endInput = document.getElementById(prefix + '_input_date_fin');

    if (!startInput || !endInput) return;

    if (startInput.value && endInput.value < startInput.value) {
        endInput.value = startInput.value;
    }
}

// --- AUTOCOMPLÉTION (Villes & Pays) ---
function setupAutocomplete(inputId, allowCountries = true) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.dataset.valid = "false";
    
    let list = document.createElement("ul");
    list.className = "suggestions-list hidden";
    input.parentNode.appendChild(list);

    let timeoutId;
    let currentController = null;

    input.addEventListener("input", function() {
        const query = this.value;
        
        input.dataset.valid = "false"; 
        list.innerHTML = "";
        list.classList.add("hidden");

        if (currentController) currentController.abort();
        clearTimeout(timeoutId);

        if (query.length < 2) return;

        timeoutId = setTimeout(async () => {
            currentController = new AbortController();
            
            try {
                let url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=fr&format=json`;
                
                const response = await fetch(url, { signal: currentController.signal });
                const data = await response.json();

                if (data.results && data.results.length > 0) {
                    let hasValidResults = false;

                    data.results.forEach(place => {
                        const isCountry = !place.admin1 && !place.admin2;

                        if (!allowCountries && isCountry) return;

                        hasValidResults = true;
                        const li = document.createElement("li");
                        li.className = "px-4 py-2 hover:bg-brand-light/30 cursor-pointer border-b border-slate-50 transition-colors flex items-center text-left";
                        
                        let icon = isCountry 
                            ? '<i class="fa-solid fa-globe text-brand-primary mr-3 text-sm"></i>'
                            : '<i class="fa-solid fa-city text-slate-300 mr-3 text-sm"></i>';
                        
                        let displayText = place.name;
                        let secondaryText = "";
                        
                        if (place.admin1) secondaryText += place.admin1;
                        if (place.country) secondaryText += (secondaryText ? ", " : "") + place.country;

                        li.innerHTML = `
                            ${icon}
                            <div class="truncate">
                                <div class="font-bold text-sm text-brand-dark">${displayText}</div>
                                <div class="text-xs text-slate-400 truncate">${secondaryText}</div>
                            </div>
                        `;

                        li.addEventListener("click", () => {
                            if (isCountry) {
                                input.value = place.name;
                                if(document.getElementById(inputId + '_lat')) document.getElementById(inputId + '_lat').value = place.latitude;
                                if(document.getElementById(inputId + '_lng')) document.getElementById(inputId + '_lng').value = place.longitude;
                                if(document.getElementById(inputId + '_type')) document.getElementById(inputId + '_type').value = 'PAYS';
                            } else {
                                input.value = `${place.name}, ${place.country || ''}`; 
                                if(document.getElementById(inputId + '_lat')) document.getElementById(inputId + '_lat').value = place.latitude;
                                if(document.getElementById(inputId + '_lng')) document.getElementById(inputId + '_lng').value = place.longitude;
                                if(document.getElementById(inputId + '_type')) document.getElementById(inputId + '_type').value = 'VILLE';
                            }
                            input.dataset.valid = "true";
                            list.classList.add("hidden");
                            list.innerHTML = "";
                        });

                        list.appendChild(li);
                    });

                    if (hasValidResults) list.classList.remove("hidden");
                }
            } catch (err) {
                if (err.name !== 'AbortError') console.error(err);
            }
        }, 150);
    });

    document.addEventListener("click", function(e) {
        if (e.target !== input && e.target !== list) {
            list.classList.add("hidden");
        }
    });
}