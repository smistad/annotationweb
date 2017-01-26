from annotationweb.models import Label


def get_complete_label_name(label):
    # If label is a sublabel this will get the label name as: "sublabel#1.name - sublabel#2.name - assignedlabel.name"
    label_name = label.name
    while label.parent is not None:
        # Get parent
        label = Label.objects.get(pk=label.parent_id)
        label_name = label.name + ' - ' + label_name

    return label_name


def get_all_labels(task):
    labels = []
    sublabels = [(x.id, x.name) for x in Label.objects.filter(task=task).order_by('-name')]
    # Create stack
    sublabel_stack = [x for x in sublabels]
    while len(sublabel_stack) > 0:
        sublabel = sublabel_stack.pop()

        sublabels = Label.objects.filter(parent_id=sublabel[0])
        for sublabel_child in sublabels:
            parent_name = sublabel[1]
            label = (sublabel_child.id, parent_name + ' - ' + sublabel_child.name)
            sublabel_stack.append(label)

        label = {'id': sublabel[0], 'name': sublabel[1]}
        labels.append(label)

    return labels
