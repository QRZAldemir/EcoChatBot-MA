import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { TurnosComponent } from './turnos.component';

const routes: Routes = [{ path: '', component: TurnosComponent }];

@NgModule({
  declarations: [TurnosComponent],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forChild(routes)
  ]
})
export class TurnosModule { }