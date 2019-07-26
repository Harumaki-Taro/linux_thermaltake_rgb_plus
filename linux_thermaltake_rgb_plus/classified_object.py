class ClassifiedObject:

    @classmethod
    def inheritors(cls):
        subclasses = set()
        work = [cls]
        while work:
            parent = work.pop()

            for child in parent.__subclasses__():
                if child not in subclasses:
                    print(child.__name__)
                    subclasses.add(child)
                    work.append(child)

        return subclasses

