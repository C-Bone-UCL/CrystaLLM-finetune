import argparse
import os
import traceback
import random
import sys
from tqdm import tqdm
from pymatgen.io.cif import CifWriter
from pymatgen.io.ase import AseAtomsAdaptor
from jarvis.db.figshare import data
from jarvis.core.atoms import Atoms
from pymatgen.core import Structure

def generate_cif(material_id, structure):
    """
    Generate a CIF string for a given material.
    """
    try:
        cif_writer = CifWriter(structure, symprec=0.1)
        cif_str = str(cif_writer)
        reduced_formula = structure.composition.reduced_formula
        comment = f"# Entry {material_id} {reduced_formula} generated using pymatgen\n"
        cif_str = comment + cif_str
        lines = cif_str.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('data_'):
                lines[i] = f"data_{reduced_formula}"
                break
        return '\n'.join(lines)
    except Exception:
        return None

def process_entry(entry, output_folder):
    """
    Convert a single entry to a .cif file and write it to the output folder.
    """
    try:
        adaptor = AseAtomsAdaptor()
        atoms_dict = entry.get('atoms')
        if atoms_dict is None:
            return

        # Convert jarvis atoms to a pymatgen structure
        atoms = Atoms.from_dict(atoms_dict)
        ase_obj = atoms.ase_converter()
        structure = adaptor.get_structure(ase_obj)

        # The jarvis-dft dataset uses 'jid' for material ID
        material_id = entry.get('jid', 'unknown_id')
        cif_str = generate_cif(material_id, structure)
        if cif_str is not None:
            cif_filename = os.path.join(output_folder, f"{material_id}.cif")
            with open(cif_filename, 'w') as f:
                f.write(cif_str)
    except Exception as e:
        print(f"Error processing entry {entry.get('jid', 'unknown_id')}: {e}")
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Generate CIF files for 1K randomly sampled jarvis-dft materials.")
    parser.add_argument("--output_folder", type=str, default="cif_output",
                        help="Folder to store the generated .cif files")
    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    try:
        # Load the jarvis-dft dataset
        jarvis_data = data("dft_3d")
    except Exception as e:
        print(f"Failed to load jarvis-dft dataset: {e}")
        sys.exit(1)

    # Randomly sample 1000 entries (or fewer if the dataset has fewer entries)
    sample_size = 1000 if len(jarvis_data) >= 1000 else len(jarvis_data)
    sampled_entries = random.sample(jarvis_data, sample_size)

    # Use tqdm to display progress
    pbar = tqdm(total=sample_size, desc="Generating CIF files", ncols=80)
    for entry in sampled_entries:
        process_entry(entry, args.output_folder)
        pbar.update(1)
    pbar.close()

    print(f"Successfully generated {sample_size} CIF files in '{args.output_folder}'.")

if __name__ == "__main__":
    main()
