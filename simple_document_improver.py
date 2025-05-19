# simple_document_improver.py

import ollama
import json
import os
import shutil 
import time
import datetime 
import logging
import random
from logging.handlers import RotatingFileHandler 

# --- Pre-Config Logging Setup ---
print("SCRIPT START: Attempting basic logging setup...\n\n")
this_file_abs_path = os.path.abspath(__file__) # Get absolute path of this script
project_root_dir = os.path.dirname(this_file_abs_path) # Get directory of this script
print(f"Project Root Directory: {project_root_dir}")
print(f"For a fresh run, you may want to delete old files/folders from:")
print(f"  - {os.path.join(project_root_dir, 'logs')}")
print(f"  - {os.path.join(project_root_dir, 'document_backups')}")
print(f"  - and reset/edit {os.path.join(project_root_dir, config.get('document_path', 'project_document.txt')) if 'config' in locals() else 'project_document.txt'}\n\n")



logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
initial_logger = logging.getLogger("PRE_CONFIG_INIT")
initial_logger.info("PRE_CONFIG_INIT: BasicConfig called.")

# --- Configuration ---
try:
    with open("simple_config.json", "r", encoding="utf-8") as f: 
        config = json.load(f)
    initial_logger.info("Successfully loaded simple_config.json")
except FileNotFoundError:
    initial_logger.warning("simple_config.json not found. Using default settings.")
    config = {}
except json.JSONDecodeError:
    initial_logger.error("Error decoding simple_config.json. Using default settings.")
    config = {}

DOCUMENT_FILE_PATH = config.get("document_path", "project_document.txt")
DOCUMENT_TITLE = config.get("document_title", "Baby Alpha: Can we build a tiny basic Python autonomous agent that copies how people brainstorm, judge, and rewrite ideas on its own? Would this back-and-forth loop stop the AI from either hallucinating or just repeating its training data, and instead spark truly new ideas? Can it take ideas from the world and combine them in truly novel ways to solve a problem? What sort of code would be needed, and how would it work? And how might an open source agent like that change the world?") 
BACKUP_DIR = "document_backups"
LLM_MODEL = config.get("gen_model", "gemma3:12b-it-qat")
TEMPERATURE_GENERAL = config.get("temperature_general", 0.6)
TEMPERATURE_BRAINSTORM_MIN = config.get("temperature_brainstorm_min", 0.5) 
TEMPERATURE_BRAINSTORM_MAX = config.get("temperature_brainstorm_max", 1.0) 
TEMPERATURE_SYNTHESIS = config.get("temperature_synthesis", 0.5)
MAX_ITERATIONS = config.get("max_iterations_simple", 500) 
MAX_BACKUP_FILES = config.get("max_backup_files", 50)
MAX_CONVO_LOG_SIZE_MB = config.get("max_convo_log_size_mb", 20)


# --- Directory Setup ---
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    initial_logger.info(f"Directories '{BACKUP_DIR}' and 'logs' ensured.")
except Exception as e:
    initial_logger.error(f"Error creating directories: {e}")

# --- Full Logging Setup ---
log_file_path = os.path.join("logs", "simple_improver.log")
logger = logging.getLogger() 
logger.setLevel(logging.INFO) 

for handler in logger.handlers[:]: logger.removeHandler(handler)

try:
    app_log_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=10*1024*1024, 
        backupCount=5, 
        encoding='utf-8',
        delay=True
    )
    app_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s")
    app_log_handler.setFormatter(app_log_formatter)
    logger.addHandler(app_log_handler)
    logging.info(f"RotatingFileHandler for main app log configured for {log_file_path}")
except Exception as e:
    initial_logger.error(f"Failed to create FileHandler for {log_file_path}: {e}")

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter("[%(levelname)s] %(message)s") 
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logging.info(f"--- Simple Document Improver Session Started (Full Logging): {datetime.datetime.now()} ---")

# --- Convo Log Setup ---
convo_log_path = os.path.join("logs", "convo_simple.txt")

def manage_convo_log_rotation():
    try:
        if os.path.exists(convo_log_path):
            if os.path.getsize(convo_log_path) > MAX_CONVO_LOG_SIZE_MB * 1024 * 1024:
                backup_convo_path = convo_log_path + ".1"
                if os.path.exists(backup_convo_path): os.remove(backup_convo_path)
                os.rename(convo_log_path, backup_convo_path)
                logging.info(f"Rotated convo_simple.txt (max size {MAX_CONVO_LOG_SIZE_MB}MB reached).")
                with open(convo_log_path, "w", encoding="utf-8") as f_conv_new:
                    f_conv_new.write(f"--- Simple Improver Convo Log (New after Rotation): {datetime.datetime.now()} ---\n")
    except Exception as e:
        logging.error(f"Error managing convo_simple.txt rotation: {e}")

# --- LLM Interaction ---
ollama_client = None
try:
    ollama_client = ollama.Client()
    ollama_client.list()
    logging.info("Ollama client initialized and server connection successful.")
except Exception as e:
    logging.critical(f"Failed to initialize Ollama client: {e}", exc_info=True)

def ask_llm(prompt_text: str, session_memory: dict, temperature: float = TEMPERATURE_GENERAL):
    if not ollama_client:
        return "Error: Ollama client not available."

    final_prompt_to_llm = (
        f"You are a critical AI co-author whose primary mission is to expand this research white paper as much as possible:\n--- "
        f"'{DOCUMENT_TITLE}' ---\n  With every response, add substantial new content—"
        f"aim for at least 400–600 fresh words per turn—and keep growing the document well past "
        f"6000 words over time. Blend proven methods from the past, cross-disciplinary insights, and bold left-field "
        f"ideas into a practical, low-cost, step-by-step solution. Justify each element with rigorous "
        f"logic and real-world analogues, devoting most of the paper to what the solution is, why it "
        f"works, and how to implement it.\n\nTASK / QUESTION:\n{prompt_text}"
    )
    logging.info(f"Sending to LLM (Temp: {temperature}):\n    prompt_text without prefix = {prompt_text[:150]}\n")
    manage_convo_log_rotation()
    try:
        with open(convo_log_path, "a", encoding="utf-8") as f_convo:
            f_convo.write(f"\n\n>>>> USER PROMPT TO LLM (Final Form) - Iteration {session_memory.get('current_iteration', 'N/A')} - {datetime.datetime.now()}:\n{final_prompt_to_llm}\n")
    except Exception as e_convo: logging.error(f"Failed to write prompt to convo_simple.txt: {e_convo}")

    try:
        response = ollama_client.generate(
            model=LLM_MODEL,
            prompt=final_prompt_to_llm,
            options={
                "temperature": temperature,
                "num_predict": config.get("number_pred_simple", 16384),
                "num_ctx": config.get("number_ctx_simple", 32768)
            }
        )
        llm_response_text = response.get("response", "").strip()
        logging.info(f"LLM Response (first 150 chars): {llm_response_text[:150]}...")
        try:
            with open(convo_log_path, "a", encoding="utf-8") as f_convo:
                f_convo.write(f"<<<< LLM RESPONSE:\n{llm_response_text}\n")
        except Exception as e_convo: logging.error(f"Failed to write LLM response to convo_simple.txt: {e_convo}")
        return llm_response_text
    except Exception as e:
        logging.error(f"Error asking LLM: {e}", exc_info=True)
        return f"Error: LLM call failed - {e}"

# --- Document Handling ---
def load_document(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Document '{file_path}' not found. Creating a default one.")
        default_content = f"TITLE: {DOCUMENT_TITLE}\n\nAbstract:\nAIs are known for being exceptionally inefficient at coming up with plausible and valid novel ideas. They are either just wrong and hallucinating or they are sticking to the strict consistency of their training data. But what if we could get it using human processes to generate ideas, save the best, and improve the ideas over and over autonomously? This document will explore the concept and potential of an AI agent designed to iteratively refine research papers and brainstorm novel solutions to complex problems.\n\nIntroduction:\nHuman beings have processes they use to solve problems. Businesses use these processes to help their teams of workers solve problems. Currently, LLMs require a human being to type in the prompts for the LLM. But more and more people are building autonomous agents that can work on something without human intervention, the Agent going through step by step to accomplish a goal. What if the goal is novel research? How could we make a super basic Python agent that iteratively improves any problem areas of a research paper with brainstorming, like putting 2 and 2 together to get something totally new? What would it look like? How would it work? What sort of libraries should it use and how should it be set up? And based on that, what sort of things could it accomplish and how could it impact the world?"
        if save_document(file_path, default_content): return default_content
        else: return f"Error: Could not create default document at {file_path}."
    except Exception as e:
        logging.error(f"Error loading document '{file_path}': {e}"); return f"Error loading document: {e}"

def save_document(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as f: f.write(content)
        logging.info(f"Document saved to '{file_path}'."); return True
    except Exception as e: logging.error(f"Error saving document '{file_path}': {e}"); return False

def manage_backups(file_path):
    try:
        backups = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.splitext(os.path.basename(file_path))[0] + "_v")],
            key=os.path.getmtime
        )
        while len(backups) >= MAX_BACKUP_FILES: 
            oldest_backup = backups.pop(0)
            os.remove(oldest_backup)
            logging.info(f"Removed oldest backup: {oldest_backup} (limit {MAX_BACKUP_FILES}).")
    except Exception as e: logging.error(f"Error managing backups: {e}")

def backup_document(file_path, version_counter):
    manage_backups(file_path)
    base_filename = os.path.basename(file_path)
    name_part, ext_part = os.path.splitext(base_filename)
    backup_file_name = f"{name_part}_v{version_counter}{ext_part if ext_part else '.txt'}"
    backup_full_path = os.path.join(BACKUP_DIR, backup_file_name)
    try:
        if not os.path.exists(file_path): logging.error(f"Cannot backup, source '{file_path}' missing."); return False
        shutil.copy2(file_path, backup_full_path)
        logging.info(f"Backup created: '{backup_full_path}'"); return True
    except Exception as e: logging.error(f"Error creating backup for '{file_path}': {e}"); return False

# --- Main Loop ---
def main_improvement_loop():
    if not ollama_client:
        print("Ollama client not available. Exiting."); logging.critical("Ollama client not available."); return

    document_content = load_document(DOCUMENT_FILE_PATH)
    if "Error:" in document_content: print(f"Could not load/create document: {document_content}"); logging.critical(f"Load/create error: {document_content}"); return
        
    version_number = 0
    try:
        existing_backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.splitext(os.path.basename(DOCUMENT_FILE_PATH))[0] + "_v")]
        if existing_backups:
            version_numbers = []
            for f_name in existing_backups:
                try: 
                    v_str = f_name.split('_v')[1].split('.')[0]
                    version_numbers.append(int(v_str))
                except (IndexError, ValueError):
                    logging.warning(f"Could not parse version from backup filename: {f_name}")
            if version_numbers:
                version_number = max(version_numbers)
                logging.info(f"Resuming version numbering from: {version_number}")
    except Exception as e: logging.error(f"Could not determine last backup version: {e}. Starting from 0.")

    session_memory = {} 

    for i in range(MAX_ITERATIONS):
        current_iter_num_for_log = i + 1
        logging.info(f"\n--- Iteration {current_iter_num_for_log} / {MAX_ITERATIONS} ---")
        print(f"\n\n{'='*10} ITERATION {current_iter_num_for_log} / {MAX_ITERATIONS} {'='*10}")
        
        session_memory['current_iteration'] = current_iter_num_for_log
        session_memory['original_document_for_iteration'] = document_content 
        accumulated_notes_for_synthesis = "" 

        # 1a. Get Pros and Cons
        prompt1a_procon = (
            f"Critically analyze the current comprehensive, extensively detailed, and thorough research white paper titled '{DOCUMENT_TITLE}'. "
            f"Your task is to provide structured feedback. Please format your response as follows:\n"
            f"PROS:\n"
            f"- [Pro 1]\n"
            f"- [Pro 2]\n"
            f"- [Pro 3 (if applicable)]\n\n" # Reduced to 3-3 for brevity, can be 3-5
            f"CONS:\n"
            f"- [Con 1 - specific weakness or area for improvement]\n"
            f"- [Con 2 - specific weakness or area for improvement]\n"
            f"- [Con 3 (if applicable) - specific weakness or area for improvement]\n\n"
            f"Focus on identifying actionable Cons. Do not state 'No Cons' in this step; strive to find areas for improvement.\n\n"
            f"CURRENT DOCUMENT:\n'''\n{document_content}\n'''"
        )
        print(f"\n{'='*5} STEP 1a!!! Asking LLM: List Pros and Cons {'='*5}")
        response_procon = ask_llm(prompt1a_procon, session_memory, temperature=TEMPERATURE_GENERAL)
        if "Error:" in response_procon: logging.error(f"LLM Error listing pros/cons: {response_procon}"); break
        
        session_memory['pros_and_cons_list'] = response_procon
        accumulated_notes_for_synthesis += f"\n\n--- Notes for Iteration {current_iter_num_for_log} ---\nPros and Cons Analysis:\n{response_procon}\n"
        logging.info(f"LLM Pros/Cons Analysis:\n{response_procon}")
        print(f"LLM Pros/Cons Analysis:\n{response_procon[:500]}...")

        # 1b. Pick the most critical Con to fix
        prompt1b_pick_con = (
            f"From the list of 'Cons' you just provided for the paper '{DOCUMENT_TITLE}':\n"
            f"'''\n{session_memory['pros_and_cons_list']}\n'''\n" 
            f"tell me Which ONE of these Cons is the single most critical or impactful one to address next to improve the paper? "
            f"If, after reviewing your own list, you genuinely believe there are NO actionable 'Cons' that can be reasonably addressed from that list, " 
            f"then and ONLY then, respond with the exact phrase 'No Actionable Cons Found'. "
            f"Otherwise, please state ONLY the chosen 'Con' you will focus on."
        )
        print(f"\n{'='*5} STEP 1b!!! Asking LLM: Pick most critical Con to fix {'='*5}")
        chosen_con_to_fix = ask_llm(prompt1b_pick_con, session_memory, temperature=TEMPERATURE_GENERAL)
        if "Error:" in chosen_con_to_fix: logging.error(f"LLM Error picking con: {chosen_con_to_fix}"); break
        
        if "no actionable cons found" in chosen_con_to_fix.strip().lower() and len(chosen_con_to_fix.strip()) < 30: # More specific check
            logging.info("LLM indicated no actionable cons found to pick from. Document considered complete by this strategy.")
            print("Process Complete! LLM found no actionable Cons to pick.")
            break
            
        session_memory['identified_problem'] = chosen_con_to_fix 
        logging.info(f"Identified problem (chosen Con): {session_memory['identified_problem']}")
        print(f"LLM chose problem to fix: {session_memory['identified_problem'][:100]}...")
        accumulated_notes_for_synthesis += f"\nChosen Problem to Address: {session_memory['identified_problem']}\n"

        # BRAINSTORMING? STEP A: Should we brainstorm to fix this con?
        prompt_should_brainstorm = (
            f"For the identified problem: '{session_memory['identified_problem']}'.\n"
            f"Is a common knowledge rewrite of the document likely to easily address this, "
            f"or would in-depth exhaustive brainstorming of diverse and novel ideas be more beneficial for a breakthrough or truly innovative solution? "
            f"Consider if the problem requires common knowledge fixes or truly novel thinking. "
            f"Respond ONLY with 'Brainstorm' or 'Direct Fix'."
        )
        print(f"\n{'='*5} BRAINSTORMING? STEP A!!! Asking LLM: Brainstorm or Direct Fix for '{session_memory['identified_problem'][:50]}...'? {'='*5}")
        decision_on_approach = ask_llm(prompt_should_brainstorm, session_memory, temperature=TEMPERATURE_GENERAL)
        if "Error:" in decision_on_approach: logging.error(f"LLM Error deciding approach: {decision_on_approach}"); continue

        if "direct fix" in decision_on_approach.strip().lower():
            print("LLM chose Direct Fix approach.")
            accumulated_notes_for_synthesis += "\nApproach Chosen: Direct Fix.\n"
            # Step 2 (Direct Fix)
            prompt2_fix = (f"For the comprehensive, extensively detailed, and thorough research white paper titled '{DOCUMENT_TITLE}'.\n"
                           f"The specific problem to fix is: '{session_memory['identified_problem']}'\n\n"
                           f"1. Please adjust only the 'targeted section' or sections that are specifically referenced or implied by the 'identified problem'. "
                           f"This might involve expanding existing paragraphs within that targeteg section, adding new paragraphs within or directly after that 'targeted section', or subtly rephrasing parts of that 'targeted section' for clarity and depth based on any straight forward obvious fixes.\n"
                           f"2. While focusing on the 'targeted section', ensure the entire document remains COHERENT and well-structured (Abstract, Introduction, Main Body, Conclusion). You may need to make minor adjustments to surrounding text for flow.\n"
                           f"3. It's okay to significantly alter or evolve previous ideas within the 'targeted section' of the 'ORIGINAL DOCUMENT CONTENT' if the new straight forward obvious fixes offer a demonstrably better approach to achieving the paper's goals, especially concerning the 'KEY PROBLEM IDENTIFIED'. Do not be afraid to replace weaker prior content within that 'targeted section' with stronger new material from the straight forward obvious fixes.\n"
                           f"4. Aim to grow the overall size and detail of the paper if the new information genuinely adds value and depth, particularly within and around the revised 'targeted section'.\n"
                           f"5. CRITICAL: Return ONLY the full text of the newly revised and integrated comprehensive, extensively detailed, and thorough research white paper. Do not include meta-commentary."
                           f"PAPER TO REVISE:\n'''\n{document_content}\n'''")
            print(f"\n{'='*5} STEP 2 (Direct Fix Path)!!! Asking LLM: Attempt to fix problem '{session_memory['identified_problem'][:50]}...' directly. {'='*5}")
            directly_fixed_version = ask_llm(prompt2_fix, session_memory, temperature=TEMPERATURE_SYNTHESIS)
            
            if "Error:" not in directly_fixed_version and len(directly_fixed_version.strip()) > 0.5 * len(document_content.strip()):
                accumulated_notes_for_synthesis += f"\nDirect Fix Attempt Content:\n'''\n{directly_fixed_version}\n'''\n"
                print("LLM provided a direct fix attempt. It will be included in synthesis notes.")
            else:
                logging.warning(f"Direct fix failed or result too short. Notes will reflect this. LLM_Fix_Response: '{directly_fixed_version[:100]}...'")
                print("LLM direct fix attempt failed or was too short.")
                accumulated_notes_for_synthesis += f"\nDirect Fix Attempt for '{session_memory['identified_problem']}': Failed or insufficient.\n"
        
        else: # Assumed "Brainstorm" or if LLM didn't say "Direct Fix" clearly
            print("LLM chose Brainstorm approach (or default).")
            accumulated_notes_for_synthesis += "\nApproach Chosen: Brainstorming.\n"
            # Steps C, D, E (Brainstorming)
            prompt_past = (f"Using brainstorming to help solve this identified problem: '{session_memory['identified_problem']}', " # Step C
                           f"list 3 distinct examples of past analogous problems (which are similar to the identified problem) and the proven methods used to fix the past problems.")
            print(f"\n{'='*5} STEP C (Brainstorm)!!! Asking LLM: Past analogies. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['brainstorm_past'] = ask_llm(prompt_past, session_memory, temperature=random_temp)
            if "Error:" not in session_memory['brainstorm_past']:
                print(f"\n{'='*5} STEP C (Brainstorm)!!! Past analogies. SUCCESS {'='*5}")

            prompt_cross = (f"Using brainstorming to help solve this identified problem: '{session_memory['identified_problem']}', " # Step D
                            f"list 3 cross-disciplinary insights or concepts (which are analogous to the concept involving the identified problem) and include how those cross-disciplinary concepts are tackling their similar problems.")
            print(f"\n{'='*5} STEP D (Brainstorm)!!! Asking LLM: Cross-field concepts. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['brainstorm_cross_field'] = ask_llm(prompt_cross, session_memory, temperature=random_temp)
            if "Error:" not in session_memory['brainstorm_cross_field']:
                print(f"\n{'='*5} STEP D (Brainstorm)!!! Cross-field concepts. SUCCESS {'='*5}")


            prompt_left = (f"Using brainstorming to help solve this identified problem: '{session_memory['identified_problem']}', " # Step E
                           f"suggest 3 bold 'left-field' analogous ideas that could lead to a solution for the identified problem.")
            print(f"\n{'='*5} STEP E (Brainstorm)!!! Asking LLM: Left-field ideas. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['brainstorm_left_field'] = ask_llm(prompt_left, session_memory, temperature=random_temp)
            if "Error:" not in session_memory['brainstorm_left_field']:
                print(f"\n{'='*5} STEP E (Brainstorm)!!! Left-field ideas. SUCCESS {'='*5}")
            
            # Step F1: Combine brainstormed ideas
            prompt_combo1 = ( # Renamed variable for clarity
                f"From all the brainstorming notes create 9 combinations. "
                f"For each combination, write out in 3 sentences about what the combination is, and what it means "
                f"in relation to the identified problem: '{session_memory['identified_problem']}', "
                f"The list will only use the first (number 1) of the Past Analogies, "
                f"then first, second, or third of the Cross-Field Concepts then first, second, or third of the Left-Field Ideas.\n\n"
                f"Complete the following list:\n"

                f"- [Past 1]+[Concept 1]+[Left-Field 1]:\n"
                f"- [Past 1]+[Concept 1]+[Left-Field 2]:\n"
                f"- [Past 1]+[Concept 1]+[Left-Field 3]:\n"
                f"- [Past 1]+[Concept 2]+[Left-Field 1]:\n"
                f"- [Past 1]+[Concept 2]+[Left-Field 2]:\n"
                f"- [Past 1]+[Concept 2]+[Left-Field 3]:\n"
                f"- [Past 1]+[Concept 3]+[Left-Field 1]:\n"
                f"- [Past 1]+[Concept 3]+[Left-Field 2]:\n"
                f"- [Past 1]+[Concept 3]+[Left-Field 3]:\n"

                f"BRAINSTORMING NOTES DUMP:\n'''\n"
                f"Past Analogies: {session_memory.get('brainstorm_past', 'N/A')}\n"
                f"Cross-Field Concepts: {session_memory.get('brainstorm_cross_field', 'N/A')}\n"
                f"Left-Field Ideas: {session_memory.get('brainstorm_left_field', 'N/A')}\n"
                f"'''")
            print(f"\n{'='*5} STEP F (Brainstorm)!!! Asking LLM: Synthesize best ideas from brainstorm. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['combo1'] = ask_llm(prompt_combo1, session_memory, temperature=random_temp) 
            if "Error:" not in session_memory['combo1']: 
                print(f"\n{'='*5} STEP F combo1 (Brainstorm)!!! SUCCESS {'='*5}")

            # Step F2: Combine brainstormed ideas
            prompt_combo2 = ( # Renamed variable for clarity
                f"From all the brainstorming notes create 9 combinations. "
                f"For each combination, write out in 3 sentences about what the combination is, and what it means "
                f"in relation to the identified problem: '{session_memory['identified_problem']}', "
                f"The list will only use the second (number 2) of the Past Analogies, "
                f"then first, second, or third of the Cross-Field Concepts then first, second, or third of the Left-Field Ideas.\n\n"
                f"Complete the following list:\n"

                f"- [Past 2]+[Concept 1]+[Left-Field 1]:\n"
                f"- [Past 2]+[Concept 1]+[Left-Field 2]:\n"
                f"- [Past 2]+[Concept 1]+[Left-Field 3]:\n"
                f"- [Past 2]+[Concept 2]+[Left-Field 1]:\n"
                f"- [Past 2]+[Concept 2]+[Left-Field 2]:\n"
                f"- [Past 2]+[Concept 2]+[Left-Field 3]:\n"
                f"- [Past 2]+[Concept 3]+[Left-Field 1]:\n"
                f"- [Past 2]+[Concept 3]+[Left-Field 2]:\n"
                f"- [Past 2]+[Concept 3]+[Left-Field 3]:\n"

                f"BRAINSTORMING NOTES DUMP:\n'''\n"
                f"Past Analogies: {session_memory.get('brainstorm_past', 'N/A')}\n"
                f"Cross-Field Concepts: {session_memory.get('brainstorm_cross_field', 'N/A')}\n"
                f"Left-Field Ideas: {session_memory.get('brainstorm_left_field', 'N/A')}\n"
                f"'''")
            print(f"\n{'='*5} STEP F (Brainstorm)!!! Asking LLM: Synthesize best ideas from brainstorm. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['combo2'] = ask_llm(prompt_combo2, session_memory, temperature=random_temp) 
            if "Error:" not in session_memory['combo2']: 
                print(f"\n{'='*5} STEP F combo2 (Brainstorm)!!! SUCCESS {'='*5}")

            # Step F3: Combine brainstormed ideas
            prompt_combo3 = ( # Renamed variable for clarity
                f"From all the brainstorming notes create 9 combinations. "
                f"For each combination, write out in 3 sentences about what the combination is, and what it means "
                f"in relation to the identified problem: '{session_memory['identified_problem']}', "
                f"The list will only use the third (number 3) of the Past Analogies, "
                f"then first, second, or third of the Cross-Field Concepts then first, second, or third of the Left-Field Ideas.\n\n"
                f"Complete the following list:\n"

                f"- [Past 3]+[Concept 1]+[Left-Field 1]:\n"
                f"- [Past 3]+[Concept 1]+[Left-Field 2]:\n"
                f"- [Past 3]+[Concept 1]+[Left-Field 3]:\n"
                f"- [Past 3]+[Concept 2]+[Left-Field 1]:\n"
                f"- [Past 3]+[Concept 2]+[Left-Field 2]:\n"
                f"- [Past 3]+[Concept 2]+[Left-Field 3]:\n"
                f"- [Past 3]+[Concept 3]+[Left-Field 1]:\n"
                f"- [Past 3]+[Concept 3]+[Left-Field 2]:\n"
                f"- [Past 3]+[Concept 3]+[Left-Field 3]:\n"

                f"BRAINSTORMING NOTES DUMP:\n'''\n"
                f"Past Analogies: {session_memory.get('brainstorm_past', 'N/A')}\n"
                f"Cross-Field Concepts: {session_memory.get('brainstorm_cross_field', 'N/A')}\n"
                f"Left-Field Ideas: {session_memory.get('brainstorm_left_field', 'N/A')}\n"
                f"'''")
            print(f"\n{'='*5} STEP F (Brainstorm)!!! Asking LLM: Synthesize best ideas from brainstorm. {'='*5}")
            random_temp = random.randint(int(TEMPERATURE_BRAINSTORM_MIN * 10), int(TEMPERATURE_BRAINSTORM_MAX * 10)) * 0.1
            session_memory['combo3'] = ask_llm(prompt_combo3, session_memory, temperature=random_temp) 
            if "Error:" not in session_memory['combo3']: 
                print(f"\n{'='*5} STEP F combo3 (Brainstorm)!!! SUCCESS {'='*5}")


            # Step G: Combine brainstormed ideas
            prompt_best4_from_brainstorm = ( # Renamed variable for clarity
                f"From all the brainstorming notes below analyze and synthesize them regarding the identified problem: '{session_memory['identified_problem']}', Write out any promising novel and actionable approaches, or key insights that could lead to a breakthrough solution.\n\n"
                f"BRAINSTORMING NOTES DUMP:\n'''\n"
                f"First Lot of Past Combinations:\n"
                f"{session_memory['combo1']}\n"
                f"Second Lot of Past Combinations:\n"
                f"{session_memory['combo2']}\n"
                f"Third Lot of Past Combinations:\n"
                f"{session_memory['combo3']}\n"
                f"'''")
            print(f"\n{'='*5} STEP F (Brainstorm)!!! Asking LLM: Synthesize best ideas from brainstorm. {'='*5}")
            session_memory['best_synthesized_brainstorm_ideas'] = ask_llm(prompt_best4_from_brainstorm, session_memory, temperature=TEMPERATURE_GENERAL) 
            if "Error:" not in session_memory['best_synthesized_brainstorm_ideas']: 
                accumulated_notes_for_synthesis += f"\nSynthesized Novel Ideas from Brainstorm:\n{session_memory['best_synthesized_brainstorm_ideas']}\n"
            
        # Final Synthesis Step for this iteration (common to both paths)
        synthesis_prompt_text = (
            f"ORIGINAL DOCUMENT\n'''\n{session_memory['original_document_for_iteration']}\n'''\n\n"
            f"IDENTIFIED PROBLEM\n'''\n{session_memory['identified_problem']}\n'''\n\n"
            f"NOTES\n'''\n{accumulated_notes_for_synthesis}\n'''\n\n"
            "INSTRUCTIONS:\n"
            "1. Locate the section(s) that address—or should address—the IDENTIFIED PROBLEM.\n"
            "2. From NOTES, pull any insights that may add depth or potentially help solve the problem.\n"
            "3. Integrate those insights into the located section(s): expand paragraphs, add new ones, or rephrase for clarity and depth.\n"
            "4. Replace weaker material in the affected section(s) with stronger content from NOTES whenever that better serves the paper’s goals.\n"
            "5. Keep the whole paper coherent and well-structured (Abstract, Introduction, Body, Conclusion); tweak nearby text as needed for flow.\n"
            "6. Return **only** the full revised paper (preferably longer than the ORIGINAL DOCUMENT). Do not include meta-commentary."
        )
        print(f"\n{'='*5} FINAL SYNTHESIS STEP!!! Asking LLM: Synthesize final paper for this iteration. {'='*5}")
        final_synthesized_version = ask_llm(synthesis_prompt_text, session_memory, temperature=TEMPERATURE_SYNTHESIS)

        if "Error:" in final_synthesized_version or len(final_synthesized_version.strip()) < 100 : 
            logging.error(f"LLM failed to synthesize or produced too short output: '{final_synthesized_version[:100]}...'. Keeping document as it was at start of iteration.")
            print("LLM synthesis failed or too short. Document for this iteration remains unchanged.")
            document_content = session_memory['original_document_for_iteration'] 
            time.sleep(1); continue 

        # Evaluate this final_synthesized_version
        prompt_evaluate = (
            f"IDENTIFIED PROBLEM:\n'''\n{session_memory.get('identified_problem','N/A')}\n'''\n\n"
            f"ORIGINAL DOCUMENT:\n'''\n{session_memory['original_document_for_iteration']}\n'''\n\n"
            f"NEW SYNTHESIZED VERSION (full text after attempting to address the problem and integrate new ideas):\n'''\n{final_synthesized_version}\n'''\n\n" 
            f"EVALUATION TASK: Compare the ORIGINAL DOCUMENT with the NEW SYNTHESIZED VERSION.\n"
            f"Answer this question: Is the 'NEW SYNTHESIZED VERSION', about the same or a better research paper than the ORIGINAL DOCUMENT? \n"
            f"If the NEW version is about the same or better, respond 'Yes'.\n"
            f"If the NEW version is worse or has introduced significant issues (i.e., it has DEGRADED), respond 'No'.\n"

            f"Respond ONLY with one word, 'Yes' (same or better) or 'No' (degraded)."
        )
        print(f"\n{'='*5} EVALUATION STEP!!! Asking LLM: Evaluate synthesized version (Yes/No). {'='*5}")
        response_evaluate = ask_llm(prompt_evaluate, session_memory, temperature=TEMPERATURE_GENERAL)

        if "Error:" in response_evaluate: logging.error(f"LLM Error evaluating: {response_evaluate}"); continue

        if response_evaluate.strip().lower() == "yes":
            logging.info("LLM confirms synthesized version is an improvement. Updating document.")
            print("LLM: Synthesized version IS an improvement. Updating.")
            version_number += 1
            if backup_document(DOCUMENT_FILE_PATH, version_number):
                document_content = final_synthesized_version 
                if not save_document(DOCUMENT_FILE_PATH, document_content):
                    logging.error("Failed to save synthesized document! Next iteration might use old content.")
            else:
                logging.warning("Failed to backup document. Not overwriting. Continuing with content from start of this iteration.")
                document_content = session_memory['original_document_for_iteration'] 
        else:
            logging.info("LLM deems synthesized version not an improvement. Reverting to document state from start of this iteration.")
            print("LLM: Synthesized version IS NOT an improvement. Reverting for this iteration.")
            document_content = session_memory['original_document_for_iteration'] 
            save_document(DOCUMENT_FILE_PATH, document_content) 

        time.sleep(1) 
    
    # Check if loop finished due to max iterations
    if 'current_iter_num_for_log' in locals() and current_iter_num_for_log == MAX_ITERATIONS : 
        logging.info(f"Reached maximum iterations ({MAX_ITERATIONS}). Stopping.")
        print(f"Reached maximum iterations ({MAX_ITERATIONS}). Final document saved as '{DOCUMENT_FILE_PATH}'.")

    save_document(DOCUMENT_FILE_PATH, document_content) 
    logging.info(f"--- Simple Document Improver Session Ended: {datetime.datetime.now()} ---")
    print(f"--- Simple Document Improver Session Ended: {datetime.datetime.now()} ---")


if __name__ == "__main__":
    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "convo_simple.txt"), "w", encoding="utf-8") as f_conv: 
            f_conv.write(f"--- Simple Improver Convo Log Started: {datetime.datetime.now()} ---\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize convo_simple.txt: {e}")

    main_improvement_loop()