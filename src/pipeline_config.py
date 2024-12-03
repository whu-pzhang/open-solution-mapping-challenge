import os

# Monkey patch collections
import collections
import collections.abc
for type_name in collections.abc.__all__:
    setattr(collections, type_name, getattr(collections.abc, type_name))

from attrdict import AttrDict

from .utils import read_config, check_env_vars

check_env_vars()

config = read_config(config_path=os.getenv('CONFIG_PATH'))
params = config.parameters

SIZE_COLUMNS = ['height', 'width']
X_COLUMNS = ['file_path_image']
Y_COLUMNS = ['file_path_mask_eroded_0_dilated_0']
Y_COLUMNS_SCORING = ['ImageId']
SEED = 1234
CATEGORY_IDS = [None, 100]
CATEGORY_LAYERS = [
    1, 1
]  # thresholds, 1 means [0.5], 19 means [0.05, ... 0.95] use only with second layer model
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

GLOBAL_CONFIG = {
    'exp_root': params.experiment_dir,
    'load_in_memory': params.load_in_memory,
    'num_workers': params.num_workers,
    'num_classes': 2,
    'img_H-W': (params.image_h, params.image_w),
    'batch_size_train': params.batch_size_train,
    'batch_size_inference': params.batch_size_inference,
    'loader_mode': params.loader_mode,
    'stream_mode': params.stream_mode
}

SOLUTION_CONFIG = AttrDict({
    'env': {
        'cache_dirpath': params.experiment_dir
    },
    'execution': GLOBAL_CONFIG,
    'xy_splitter': {
        'x_columns': X_COLUMNS,
        'y_columns': Y_COLUMNS,
    },
    'reader_single': {
        'x_columns': X_COLUMNS,
        'y_columns': Y_COLUMNS,
    },
    'loader': {
        'dataset_params': {
            'h_pad': params.h_pad,
            'w_pad': params.w_pad,
            'h': params.image_h,
            'w': params.image_w,
            'pad_method': params.pad_method
        },
        'loader_params': {
            'training': {
                'batch_size': params.batch_size_train,
                'shuffle': True,
                'num_workers': params.num_workers,
                'pin_memory': params.pin_memory
            },
            'inference': {
                'batch_size': params.batch_size_inference,
                'shuffle': False,
                'num_workers': params.num_workers,
                'pin_memory': params.pin_memory
            },
        },
    },
    'unet': {
        'architecture_config': {
            'model_params': {
                'n_filters': params.n_filters,
                'conv_kernel': params.conv_kernel,
                'pool_kernel': params.pool_kernel,
                'pool_stride': params.pool_stride,
                'repeat_blocks': params.repeat_blocks,
                'batch_norm': params.use_batch_norm,
                'dropout': params.dropout_conv,
                'in_channels': params.image_channels,
                'out_channels': params.channels_per_output,
                'nr_outputs': params.nr_unet_outputs,
                'encoder': params.encoder
            },
            'optimizer_params': {
                'lr': params.lr,
            },
            'regularizer_params': {
                'regularize': True,
                'weight_decay_conv2d': params.l2_reg_conv,
            },
            'weights_init': {
                'function': 'he',
            },
            'loss_weights': {
                'bce_mask': params.bce_mask,
                'dice_mask': params.dice_mask,
            },
            'weighted_cross_entropy': {
                'w0': params.w0,
                'sigma': params.sigma,
                'imsize': (params.image_h, params.image_w)
            },
            'dice': {
                'smooth': params.dice_smooth,
                'dice_activation': params.dice_activation
            },
        },
        'training_config': {
            'epochs': params.epochs_nr,
        },
        'callbacks_config': {
            'model_checkpoint': {
                'filepath':
                os.path.join(GLOBAL_CONFIG['exp_root'], 'checkpoints', 'unet',
                             'best.torch'),
                'epoch_every':
                1,
                'minimize':
                not params.validate_with_map
            },
            'exp_lr_scheduler': {
                'gamma': params.gamma,
                'epoch_every': 1
            },
            'plateau_lr_scheduler': {
                'lr_factor': params.lr_factor,
                'lr_patience': params.lr_patience,
                'epoch_every': 1
            },
            'training_monitor': {
                'batch_every': 1,
                'epoch_every': 1
            },
            'experiment_timing': {
                'batch_every': 10,
                'epoch_every': 1
            },
            'validation_monitor': {
                'epoch_every': 1,
                'data_dir': params.data_dir,
                'validate_with_map': params.validate_with_map,
                'small_annotations_size': params.small_annotations_size,
            },
            'neptune_monitor': {
                'model_name': 'unet',
                'image_nr': 16,
                'image_resize': 0.2,
                'outputs_to_plot': params.unet_outputs_to_plot
            },
            'early_stopping': {
                'patience': params.patience,
                'minimize': not params.validate_with_map
            },
        },
    },
    'tta_generator': {
        'flip_ud': True,
        'flip_lr': True,
        'rotation': True,
        'color_shift_runs': False
    },
    'tta_aggregator': {
        'method': params.tta_aggregation_method,
        'num_threads': params.num_threads
    },
    'postprocessor': {
        'mask_dilation': {
            'dilate_selem_size': params.dilate_selem_size
        },
        'mask_erosion': {
            'erode_selem_size': params.erode_selem_size
        },
        'prediction_crop': {
            'h_crop': params.crop_image_h,
            'w_crop': params.crop_image_w
        },
        'scoring_model': params.scoring_model,
        'lightGBM': {
            'model_params': {
                'learning_rate': params.lgbm__learning_rate,
                'boosting_type': 'gbdt',
                'objective': 'regression',
                'metric': 'regression_l2',
                'sub_feature': 1.0,
                'num_leaves': params.lgbm__num_leaves,
                'min_data': params.lgbm__min_data,
                'max_depth': params.lgbm__max_depth,
                'num_threads': params.num_threads
            },
            'training_params': {
                'number_boosting_rounds': params.lgbm__number_of_trees,
                'early_stopping_rounds': params.lgbm__early_stopping
            },
            'train_size': params.lgbm__train_size,
            'target': params.lgbm__target
        },
        'random_forest': {
            'train_size': params.lgbm__train_size,
            'target': params.lgbm__target,
            'model_params': {
                'n_estimators': params.rf__n_estimators,
                'criterion': params.rf__criterion,
                'max_depth': params.rf__max_depth,
                'min_samples_split': params.rf__min_samples_split,
                'min_samples_leaf': params.rf__min_samples_leaf,
                'max_features': params.rf__max_features,
                'max_leaf_nodes': params.rf__max_leaf_nodes,
                'n_jobs': params.rf__n_jobs,
                'verbose': params.rf__verbose,
            }
        },
        'nms': {
            'iou_threshold': params.nms__iou_threshold,
            'num_threads': params.num_threads
        },
    }
})
