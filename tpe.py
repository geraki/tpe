import pywikibot
import mwparserfromhell  # Για την ανάλυση του wikitext
import csv
import argparse  # Για την υποστήριξη command line arguments

# Σύνδεση με την ελληνική Wikipedia
site = pywikibot.Site('el', 'wikipedia')

def clean_param_value(value):
    """
    Καθαρίζει τις τιμές των παραμέτρων από ειδικούς χαρακτήρες (newline, tab κτλ.).
    """
    # Αντικατάσταση newline και tab χαρακτήρων με κενό
    cleaned_value = value.replace('\n', ' ').replace('\t', ' ')
    # Αφαίρεση περιττών λευκών χαρακτήρων στις άκρες
    return cleaned_value.strip()

def get_template_data(template_name):
    """
    Εντοπίζει όλες τις σελίδες που χρησιμοποιούν ένα πρότυπο και επιστρέφει τις τιμές των παραμέτρων.

    Args:
    template_name (str): Το όνομα του προτύπου.

    Returns:
    List of Dicts: Λίστα από λεξικά που περιέχουν τις τιμές των παραμέτρων.
    """
    template_data = []

    # Χρησιμοποιούμε το 'search' για να βρούμε σελίδες με το πρότυπο
    template = pywikibot.Page(site, 'Template:' + template_name)
    transclusions = template.getReferences(only_template_inclusion=True)

    # Για κάθε σελίδα που χρησιμοποιεί το πρότυπο
    for page in transclusions:
        try:
            # Λήψη κώδικα της σελίδας
            text = page.get()

            # Ανάλυση κώδικα της σελίδας
            wikicode = mwparserfromhell.parse(text)

            # Εύρεση του προτύπου στη σελίδα (μόνο στο ανώτερο επίπεδο)
            templates = wikicode.filter_templates(recursive=False)
            for temp in templates:
                if temp.name.matches(template_name):
                    # Συλλογή παραμέτρων και τιμών
                    params = {}
                    for param in temp.params:
                        param_name = str(param.name).strip()
                        param_value = clean_param_value(str(param.value).strip())
                        params[param_name] = param_value

                    # Αποθήκευση των παραμέτρων για αυτή τη σελίδα
                    template_data.append({'page_title': page.title(), 'params': params})

        except Exception as e:
            print(f"Σφάλμα στη σελίδα {page.title()}: {e}")

    return template_data

def create_tsv(template_name):
    """
    Δημιουργεί ένα αρχείο TSV με τις τιμές των παραμέτρων για κάθε χρήση του προτύπου.

    Args:
    template_name (str): Το όνομα του προτύπου.
    """
    data = get_template_data(template_name)

    if not data:
        print(f"Δεν βρέθηκαν χρήσεις του προτύπου {template_name}.")
        return

    # Εύρεση όλων των μοναδικών παραμέτρων από όλα τα λήμματα
    all_params = set()
    for entry in data:
        all_params.update(entry['params'].keys())

    all_params = sorted(all_params)  # Ταξινόμηση παραμέτρων

    # Δημιουργία αρχείου TSV
    tsv_filename = f"{template_name}_parameters.tsv"
    with open(tsv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter='\t')  # Χρήση tab ως διαχωριστή

        # Δημιουργία κεφαλίδων (πρώτη στήλη τα λήμματα, μετά οι παράμετροι)
        header = ['Page Title'] + all_params
        writer.writerow(header)

        # Συμπλήρωση των δεδομένων για κάθε σελίδα
        for entry in data:
            row = [entry['page_title']]  # Πρώτη στήλη το όνομα της σελίδας
            for param in all_params:
                # Γράφουμε την τιμή της κάθε παραμέτρου, ή κενό αν δεν υπάρχει
                value = entry['params'].get(param, '')  # Χρήση κενής τιμής αν η παράμετρος δεν υπάρχει
                row.append(value)
            writer.writerow(row)

    print(f"Το αρχείο TSV αποθηκεύτηκε ως '{tsv_filename}'.")

if __name__ == "__main__":
    # Χρήση της argparse για να λάβουμε το όνομα του προτύπου από την command line
    parser = argparse.ArgumentParser(description="Εξαγωγή παραμέτρων προτύπου σε αρχείο TSV")
    parser.add_argument('-t', '--template', type=str, help='Το όνομα του προτύπου που θέλεις να αναζητήσεις')
    
    # Ανάγνωση των arguments
    args = parser.parse_args()

    # Έλεγχος αν δόθηκε το όνομα του προτύπου μέσω command line
    if args.template:
        template_name = args.template
    else:
        # Ζήτηση του ονόματος του προτύπου από τον χρήστη αν δεν δόθηκε από την command line
        template_name = input("Δώσε το όνομα του προτύπου: ")

    create_tsv(template_name)
