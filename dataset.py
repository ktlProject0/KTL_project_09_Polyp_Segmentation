import os
import glob
from natsort import natsorted
import numpy as np
import pandas as pd
import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2
from torch.utils.data import Dataset
from torchvision.datasets.folder import default_loader

class CustomDataset(Dataset):
    def __init__(self,direc,mode='eval'):
        
        img_path = natsorted(glob.glob(os.path.join(direc,'images','*')))
        mask_path = natsorted(glob.glob(os.path.join(direc,'masks','*')))
        self.meta_df = pd.DataFrame({"image":img_path,'label':mask_path})
        if mode =='train':
            self.transform = A.Compose([
                    A.Resize(width=224, height=224),
                    A.HorizontalFlip(),
                    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
                    A.ShiftScaleRotate(shift_limit=(-0.05,0.05),scale_limit=(-0.1,0.2),rotate_limit=(-10,10),p=0.5),
                    A.Normalize(mean=0.5, 
                                std=0.5, 
                                max_pixel_value=1.0, always_apply=True, p=1.0),
                    ToTensorV2(transpose_mask=True)
                ])
        elif mode=='eval':
            self.transform = A.Compose([
    A.Resize(width=224, height=224),
    A.Normalize(mean=0.5, 
                std=0.5, 
                max_pixel_value=1.0, always_apply=True, p=1.0),
    ToTensorV2(transpose_mask=True)
])
        
        self.cache={}
        
    def __len__(self):
        return len(self.meta_df)

    
    def __getitem__(self,idx):
        if idx in self.cache:
            sample = self.cache[idx]
        else:
            sample = self.meta_df.iloc[idx,:].to_dict()
            
            image = (np.array(default_loader(sample['image']))/255.).astype(np.float32)
            mask = np.array(default_loader(sample['label']))[...,0]
            mask = mask>100
            mask = np.stack([(mask==x).astype(np.uint8) for x in [0,1]], axis=-1)

            sample['image'] = image
            sample['mask'] = mask
            sample['origin_shape'] = image.shape

            self.cache[idx] = sample
            
        if self.transform:
            transformed = self.transform(image= sample['image'], mask = sample['mask'])

        sample_input = {}
        sample_input['input'] = transformed['image']
        sample_input['target'] = transformed['mask']
        sample_input['origin_shape'] = sample['origin_shape']
        
        return sample_input
        
if __name__ == '__main__':
    train = CustomDataset('/home/hjy/jiyong/synology/jiyong/stomach_1/','train')
    test = CustomDataset('/home/hjy/jiyong/synology/jiyong/stomach_1/','test')
    for sample_input in train:
        print(sample_input['input'].shape)
        print(sample_input['target'].shape)