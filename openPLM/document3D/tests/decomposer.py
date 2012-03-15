from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.document3D.models import  Document3DController , ArbreFile ,GeometryFile
from openPLM.plmapp.models import  DocumentFile
from django.core.files import File
from openPLM.document3D.arborescense import read_ArbreFile
from openPLM.document3D.decomposer import decomposer_all , diviser , is_decomposable , decomposer_product
from openPLM.document3D.STP_converter_WebGL import NEW_STEP_Import ,GetLabelNom
from OCC.TDF import *
class decomposer_Test(CommonViewTest):

    def setUp(self):
        super(decomposer_Test, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        myfile.name="test.stp"
        self.stp=self.document.add_file(myfile)

        self.list_document_controller=[]
        self.list_document_controller.append(Document3DController.create('doc2', 'Document3D',
                'a', self.user, self.DATA))
        self.list_document_controller.append(Document3DController.create('doc3', 'Document3D',
                'a', self.user, self.DATA))                                       
        self.links=read_ArbreFile(self.stp).links
        self.my_step_importer=NEW_STEP_Import(self.stp)
        self.product=self.my_step_importer.generate_product_arbre() 
    
    def test_decomposer_all_and_deprecated_original(self):
        """
        Decompose a file step and then to depreciate it manually
        """

        self.assertEqual(len(ArbreFile.objects.all()),1)
        self.assertEqual(len(GeometryFile.objects.all()),3)
            
        to_index=decomposer_all(self.stp,self.list_document_controller,self.user)
        self.assertEqual(len(ArbreFile.objects.all()),4)
        self.assertEqual(len(GeometryFile.objects.all()),6) 
              
        self.document.deprecate_file(self.stp) 
        self.assertEqual(len(ArbreFile.objects.all()),3)
        self.assertEqual(len(GeometryFile.objects.all()),3)
          
        new_stp=self.document.files[0]
        self.assertEqual(len(to_index),3)
        self.assertEqual(read_ArbreFile(new_stp).links,[])

        self.assertEqual(len(DocumentFile.objects.all()),4)        
        self.assertEqual(len(DocumentFile.objects.all().exclude(deprecated=True)),3)         
             
    def test_decomposer_all_raises_to_delete(self):
        """
        Decompose a file step without valids controllers for childs and there checks the generation of to_delete
        Decompose a file step without valids GeometryFiles and there checks the generation of to_delete
        """

        try:
            to_index=decomposer_all(self.stp,[1,2],self.user)
        except Exception as excep:
            self.assertEqual(len(excep.to_delete),1)
    
        GeometryFile.objects.all()[2].delete()
        try:
            to_index=decomposer_all(self.stp,self.list_document_controller,self.user)
        except Exception as excep:
            self.assertEqual(len(excep.to_delete),5) 
            
    def test_diviser(self):

        to_delete=[]
        to_index=[]
        diviser(self.product.links[1].product,self.list_document_controller[0],to_delete,to_index)
        self.assertEqual(len(to_delete),4)        
        self.assertEqual(len(to_index),1)
        self.assertEqual(len(ArbreFile.objects.all()),2)
        self.assertEqual(len(GeometryFile.objects.all()),5)
            
            
    def test_is_decomposable(self):

        self.assertTrue(is_decomposable(self.document))
        self.assertFalse(is_decomposable(self.list_document_controller[0]))
        
        native=self.document.add_file(self.get_file("test.fcstd"))
        self.document.lock(native)
        self.assertFalse(is_decomposable(self.document))
        
        self.document.unlock(native)
        self.document.lock(self.stp)
        self.assertFalse(is_decomposable(self.document))
        

    def test_decomposer_product(self):
    
    
        to_delete=[]
        to_index=[]
        doc_file=decomposer_product(self.product,self.my_step_importer,self.stp,self.user,to_delete,to_index)   
        self.assertEqual(len(to_delete),2)        
        self.assertEqual(len(to_index),1)
        

        product=read_ArbreFile(doc_file)       
         
        self.assertEqual(self.product.name,product.name)
        self.assertEqual(self.product.links,product.links,[])
        
        

"""        
def decomposer_product(product,my_step_importer,stp_file,user,to_delete,to_index):



    
    
    Doc_controller=get_controller(stp_file.document.type)
    Doc_controller=Doc_controller(stp_file.document,user)




       
    
    for i in range(labels_roots.Length()):
        if shape_tool.IsAssembly(labels_roots.Value(i+1)):
            l_c = TDF_LabelSequence()
            shape_tool.GetComponents(labels_roots.Value(i+1),l_c)
            for e in range(l_c.Length()):
                shape_tool.RemoveComponent(l_c.Value(e+1))


    doc_file=generate_DocumentFile(product,Doc_controller,labels_roots.Value(1),stp_file.filename,to_delete,to_index)
    product.links=[]
    product.doc_id=doc_file.id
    to_delete.append(write_ArbreFile(product,doc_file))
"""   