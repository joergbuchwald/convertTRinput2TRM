import sys
from ogs6py.ogs import OGS


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Requires two arguments, input and output file names.")
        exit

    model = OGS(INPUT_FILE=sys.argv[1], PROJECT_FILE=sys.argv[2])

    model.replace_text("THERMO_RICHARDS_MECHANICS", xpath="./processes/process/name")
    dim = len(model.tree.find("./processes/process/specific_body_force").text.split(" "))
    model.add_entry("./processes/process/process_variables",tag="displacement", text="displacement")
    model.remove_element(xpath="./processes/process/simplified_elasticity")
    media = model.tree.findall("./media/medium")
    for i, m in enumerate(media):
        #/phase[type='Solid']/property[name='youngs_modulus']/value
        E = m.find("./phases/phase[type='Solid']/properties/property[name='youngs_modulus']/value").text
        nu = m.find("./phases/phase[type='Solid']/properties/property[name='poissons_ratio']/value").text
        E_list = E.split(" ")
        nu_list = nu.split(" ")
        G12 = float(E_list[0])/(2*(1+float(nu_list[0])))
        Gunknown = G12
        if len(E_list) > 1:
            model.add_block("constituitive_relation", block_attrib={"id": str(i)} , parent_xpath="./processes/process", taglist=["type", "youngs_moduli", "shear_moduli", "poissons_ratios"], textlist=["LinearElasticOrthotropic", f"E{str(i)}", f"G{str(i)}", f"nu{str(i)}"])
            model.add_block("parameter", parent_xpath="./parameters", taglist=["name", "type", "values"], textlist=[f"E{str(i)}", "Constant",E])
            model.add_block("parameter", parent_xpath="./parameters", taglist=["name", "type", "values"], textlist=[f"G{str(i)}", "Constant",f"{G12} {Gunknown} {Gunknown}"])
            model.add_block("parameter", parent_xpath="./parameters", taglist=["name", "type", "values"], textlist=[f"nu{str(i)}", "Constant",nu])
        else:
            model.add_block("constituitive_relation", block_attrib={"id": str(i)} , parent_xpath="./processes/process", taglist=["type", "youngs_modulus", "poissons_ratio"], textlist=["LinearElasticIsotropic", f"E{str(i)}", f"nu{str(i)}"])
            model.add_block("parameter", parent_xpath="./parameters", taglist=["name", "type", "values"], textlist=[f"E{str(i)}", "Constant",E])
            model.add_block("parameter", parent_xpath="./parameters", taglist=["name", "type", "values"], textlist=[f"nu{str(i)}", "Constant",nu])
    model.remove_element("./media/medium/phases/phase[type='Solid']/properties/property[name='youngs_modulus']")
    model.remove_element("./media/medium/phases/phase[type='Solid']/properties/property[name='poissons_ratio']")
    abstols = model.tree.find("./time_loop/processes/process/convergence_criterion/abstols")
    reltols = model.tree.find("./time_loop/processes/process/convergence_criterion/reltols")
    if reltols is not None:
        tols_list = reltols.text.split(" ")
    elif abstols is not None:
        tols_list = abstols.text.split(" ")
    else:
        print("could not find reltols or abstols")
        raise RuntimeError
    if dim == 1:
        tols = f"{tols_list[0]} {tols_list[1]} {tols_list[1]}"
    elif dim == 2:
        tols = f"{tols_list[0]} {tols_list[1]} {tols_list[1]} {tols_list[1]}"
    else:
        tols = f"{tols_list[0]} {tols_list[1]} {tols_list[1]} {tols_list[1]}  {tols_list[1]}"
    if reltols is not None:
        reltols.text = tols
    elif abstols is not None:
        abstols_list = tols
    model.add_entry(parent_xpath="./time_loop/output/variables", tag="variable", text="displacement")
    model.add_block("process_variable", parent_xpath="./process_variables", taglist=["name","components", "order","initial_condition"], textlist=["displacement",str(dim),"1","displacement_ic"])
    model.write_input()